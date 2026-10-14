"""Registrasi pasien singkat dan kunjungan (FR-02, Desain 2.2)."""

import math
import re
import time
import uuid
from dataclasses import dataclass

from flask import current_app
from limits import parse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.extensions import db, limiter
from app.models import Kunjungan, Pasien, Pengguna
from app.models.enums import AksiAudit, StatusKunjungan
from app.services.audit_logger import AuditLogger
from app.utils.errors import KonflikError, TerlaluBanyakPercobaanError, TidakDitemukanError, ValidasiGagalError
from app.utils.schemas import RegistrasiRequest
from app.utils.waktu import sekarang, usia_pasien

MAKS_HASIL_PENCARIAN = 20
STATUS_AKTIF = (StatusKunjungan.MENUNGGU, StatusKunjungan.DITANGANI)
POLA_NIK = re.compile(r"[0-9]{16}")

# Perubahan status yang sah (keputusan K9). Status lain, termasuk mundur, dibalas 409.
TRANSISI_STATUS = {
    StatusKunjungan.MENUNGGU: (StatusKunjungan.DITANGANI, StatusKunjungan.SELESAI),
    StatusKunjungan.DITANGANI: (StatusKunjungan.SELESAI,),
    StatusKunjungan.SELESAI: (),
}


@dataclass(frozen=True)
class HasilCari:
    pasien: Pasien
    id_kunjungan_aktif: uuid.UUID | None


@dataclass(frozen=True)
class HasilRegistrasi:
    kunjungan: Kunjungan
    pasien_baru: bool


def samarkan_nik(nik: str | None) -> str | None:
    return None if nik is None else "*" * 12 + nik[-4:]


def _nama_baku(nama: str) -> str:
    return " ".join(nama.split()).casefold()


def _escape_like(teks: str) -> str:
    return teks.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _subquery_kunjungan_aktif():
    return (
        select(Kunjungan.id_kunjungan)
        .where(Kunjungan.id_pasien == Pasien.id_pasien, Kunjungan.status.in_(STATUS_AKTIF))
        .order_by(Kunjungan.waktu_datang.desc())
        .limit(1)
        .scalar_subquery()
    )


class PembatasCariNik:
    """Pencarian NIK yang tidak menemukan pasien dihitung per akun (keputusan pencarian NIK, pilihan b).

    Penyimpanannya sama dengan pembatas login (Flask-Limiter), tetapi hitungan hanya ditambah setelah
    hasilnya diketahui kosong, sehingga pencarian NIK yang berhasil dan pencarian nama tidak dibatasi.
    """

    def __init__(self, pengguna: Pengguna) -> None:
        self.item = parse(current_app.config["BATAS_CARI_NIK"])
        self.kunci = f"cari-nik:{pengguna.id_pengguna}"

    def periksa(self) -> None:
        if not limiter.enabled or limiter.limiter.test(self.item, self.kunci):
            return
        reset = limiter.limiter.get_window_stats(self.item, self.kunci).reset_time
        raise TerlaluBanyakPercobaanError(
            "Terlalu banyak pencarian NIK yang tidak ditemukan. Coba lagi beberapa saat lagi, atau cari dengan nama.",
            max(1, math.ceil(reset - time.time())),
        )

    def catat_tidak_ditemukan(self) -> None:
        if limiter.enabled:
            limiter.limiter.hit(self.item, self.kunci)


class KunjunganService:
    def cari_pasien(self, q: str) -> list[HasilCari]:
        """NIK lengkap dicocokkan persis; selain itu dicari di nama tanpa membedakan huruf besar."""
        kueri = select(Pasien, _subquery_kunjungan_aktif().label("id_kunjungan_aktif"))
        if POLA_NIK.fullmatch(q):
            kueri = kueri.where(Pasien.nik == q)
        else:
            kueri = kueri.where(Pasien.nama.ilike(f"%{_escape_like(q)}%", escape="\\"))
        kueri = kueri.order_by(Pasien.nama, Pasien.id_pasien).limit(MAKS_HASIL_PENCARIAN)
        return [HasilCari(pasien=pasien, id_kunjungan_aktif=aktif) for pasien, aktif in db.session.execute(kueri)]

    def cari_pasien_oleh(self, q: str, pengguna: Pengguna) -> list[HasilCari]:
        if not POLA_NIK.fullmatch(q):
            return self.cari_pasien(q)
        pembatas = PembatasCariNik(pengguna)
        pembatas.periksa()
        hasil = self.cari_pasien(q)
        if not hasil:
            pembatas.catat_tidak_ditemukan()
        return hasil

    def ubah_status(self, id_kunjungan: uuid.UUID, status: StatusKunjungan) -> Kunjungan:
        try:
            kunjungan = db.session.scalar(
                select(Kunjungan)
                .where(Kunjungan.id_kunjungan == id_kunjungan)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
            if kunjungan is None:
                raise TidakDitemukanError("Kunjungan tidak ditemukan.")
            if status not in TRANSISI_STATUS[kunjungan.status]:
                raise KonflikError(
                    f"Status kunjungan tidak bisa diubah dari {kunjungan.status.value} ke {status.value}."
                )
            if status == StatusKunjungan.DITANGANI:
                kunjungan.waktu_ditangani = sekarang()
            kunjungan.status = status
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        db.session.refresh(kunjungan)
        return kunjungan

    def daftar(self, data: RegistrasiRequest, perawat: Pengguna) -> HasilRegistrasi:
        """Membuat kunjungan berstatus menunggu. Pasien, kunjungan, dan log audit masuk satu transaksi."""
        try:
            pasien, pasien_baru = self._pasien_untuk(data, perawat)
            aktif = db.session.scalar(
                select(Kunjungan.id_kunjungan).where(
                    Kunjungan.id_pasien == pasien.id_pasien, Kunjungan.status.in_(STATUS_AKTIF)
                )
            )
            if aktif is not None:
                raise KonflikError(
                    "Pasien ini masih punya kunjungan yang menunggu atau sedang ditangani.",
                    ekstra={"id_kunjungan_aktif": str(aktif)},
                )
            kunjungan = Kunjungan(id_pasien=pasien.id_pasien)
            db.session.add(kunjungan)
            db.session.flush()
            AuditLogger().catat(
                AksiAudit.REGISTRASI_KUNJUNGAN,
                perawat,
                # Tanpa nama dan NIK; cukup id supaya log audit tidak menyalin data pribadi.
                catatan=(
                    f"id_kunjungan={kunjungan.id_kunjungan}; id_pasien={pasien.id_pasien}; "
                    f"pasien_baru={'ya' if pasien_baru else 'tidak'}"
                ),
            )
            db.session.commit()
        except IntegrityError as galat:
            db.session.rollback()
            # Dua registrasi bersamaan dengan NIK baru yang sama: yang kalah mendapat 409, bukan 500.
            if getattr(getattr(galat.orig, "diag", None), "constraint_name", None) == "uq_pasien_nik":
                raise KonflikError(
                    "NIK ini baru saja didaftarkan. Cari pasien dengan NIK tersebut lalu pilih dari hasil pencarian."
                ) from galat
            raise
        except Exception:
            db.session.rollback()
            raise
        db.session.refresh(kunjungan)
        return HasilRegistrasi(kunjungan=kunjungan, pasien_baru=pasien_baru)

    def _pasien_untuk(self, data: RegistrasiRequest, perawat: Pengguna) -> tuple[Pasien, bool]:
        if data.id_pasien is not None:
            # Dikunci supaya dua registrasi bersamaan untuk pasien yang sama tidak sama-sama lolos cek kunjungan aktif.
            pasien = db.session.scalar(select(Pasien).where(Pasien.id_pasien == data.id_pasien).with_for_update())
            if pasien is None:
                raise ValidasiGagalError([{"field": "id_pasien", "pesan": "Pasien tidak ditemukan."}])
            return pasien, False

        self._periksa_identitas(data)
        if data.nik is not None:
            terdaftar = self._pasien_dengan_nik(data.nik)
            if terdaftar is not None:
                if _nama_baku(terdaftar.nama) != _nama_baku(data.nama) or terdaftar.jenis_kelamin != data.jenis_kelamin:
                    raise KonflikError(
                        "NIK sudah terdaftar atas pasien lain. Periksa kembali NIK, atau pilih pasien dari hasil "
                        "pencarian."
                    )
                return terdaftar, False

        pasien = Pasien(
            didaftarkan_oleh=perawat.id_pengguna,
            nama=data.nama,
            tanggal_lahir=data.tanggal_lahir,
            perkiraan_usia=data.perkiraan_usia,
            jenis_kelamin=data.jenis_kelamin,
            nik=data.nik,
            no_telepon=data.no_telepon,
        )
        db.session.add(pasien)
        db.session.flush()
        return pasien, True

    @staticmethod
    def _pasien_dengan_nik(nik: str) -> Pasien | None:
        return db.session.scalar(select(Pasien).where(Pasien.nik == nik).with_for_update())

    @staticmethod
    def _periksa_identitas(data: RegistrasiRequest) -> None:
        galat = []
        if data.nama is None:
            galat.append({"field": "nama", "pesan": "Nama wajib diisi."})
        if data.jenis_kelamin is None:
            galat.append({"field": "jenis_kelamin", "pesan": "Jenis kelamin wajib diisi."})
        if data.tanggal_lahir is None and data.perkiraan_usia is None:
            galat.append({"field": "tanggal_lahir", "pesan": "Isi tanggal lahir atau perkiraan usia."})
        if galat:
            raise ValidasiGagalError(galat)


def usia(pasien: Pasien) -> int | None:
    return usia_pasien(pasien.tanggal_lahir, pasien.perkiraan_usia)
