"""Input triase dan rekomendasi risk level (FR-03, FR-05, Desain 2.3 dan 2.5)."""

import uuid
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import exists, select

from app.ai.klasifikasi import FiturTriase, buat_klasifikator
from app.ai.penjelasan import format_angka
from app.ai.registry import ModelRegistry
from app.extensions import db
from app.models import Kunjungan, LogAudit, PemindaianAlat, Pengguna, Triase
from app.models.enums import AksiAudit, JenisTriase, StatusKunjungan, SumberTandaVital
from app.services.konfigurasi_service import CacheKonfigurasi
from app.utils.errors import KonflikError, TidakDitemukanError, ValidasiGagalError
from app.utils.schemas import Peringatan, TandaVital, TriaseInput
from app.utils.waktu import WIB, hari_ini, usia_pasien

KOLOM_TANDA_VITAL = ("td_sistolik", "td_diastolik", "nadi", "laju_napas", "suhu", "saturasi")
# Data latih model mulai usia sekitar 15 tahun (ml-service/triase_data.py, kelompok usia).
USIA_MINIMAL_DATA_LATIH = 15


@dataclass(frozen=True)
class BatasVital:
    field: str
    label: str
    satuan: str
    salah_ketik_bawah: float
    salah_ketik_atas: float
    klinis_bawah: float | None
    klinis_atas: float | None


# Dua lapis (keputusan K4): batas "tidak lazim" dari prototipe (lib/vital-warnings.ts) untuk menangkap
# salah ketik, lalu ambang klinis. Batas bawah klinis dipakai dengan "<", batas atas dengan ">=".
BATAS_VITAL = (
    BatasVital("td_sistolik", "Tekanan darah sistolik", " mmHg", 40, 260, 90, 180),
    BatasVital("td_diastolik", "Tekanan darah diastolik", " mmHg", 20, 180, None, 120),
    BatasVital("nadi", "Nadi", " x/menit", 20, 250, 50, 130),
    BatasVital("laju_napas", "Laju napas", " x/menit", 5, 60, 10, 30),
    BatasVital("suhu", "Suhu tubuh", " °C", 30, 43, 35, 39),
    BatasVital("saturasi", "Saturasi oksigen", "%", 0, 100, 90, None),
)


def _nilai_json(nilai: int | Decimal) -> int | float:
    return float(nilai) if isinstance(nilai, Decimal) else nilai


class PeringatanVital:
    """Menandai nilai tanda vital yang mungkin tetapi tidak wajar, tanpa menolak request (Desain 2.3)."""

    @staticmethod
    def periksa(tv: TandaVital) -> list[Peringatan]:
        hasil: list[Peringatan] = []
        for batas in BATAS_VITAL:
            nilai = getattr(tv, batas.field)
            teks = f"{batas.label} {format_angka(nilai)}{batas.satuan}"
            path = f"tanda_vital.{batas.field}"
            if nilai < batas.salah_ketik_bawah or nilai > batas.salah_ketik_atas:
                hasil.append(Peringatan(field=path, pesan=f"{teks} tidak lazim. Pastikan tidak salah ketik."))
            elif batas.klinis_bawah is not None and nilai < batas.klinis_bawah:
                pesan = f"{teks} di bawah batas wajar (< {format_angka(batas.klinis_bawah)}{batas.satuan})."
                hasil.append(Peringatan(field=path, pesan=pesan))
            elif batas.klinis_atas is not None and nilai >= batas.klinis_atas:
                pesan = f"{teks} melewati batas wajar (≥ {format_angka(batas.klinis_atas)}{batas.satuan})."
                hasil.append(Peringatan(field=path, pesan=pesan))
        if tv.td_diastolik >= tv.td_sistolik:
            hasil.append(
                Peringatan(
                    field="tanda_vital.td_diastolik",
                    pesan=(
                        f"Tekanan darah diastolik ({tv.td_diastolik} mmHg) tidak lebih rendah dari sistolik "
                        f"({tv.td_sistolik} mmHg). Pastikan nilainya tidak tertukar."
                    ),
                )
            )
        return hasil

    @staticmethod
    def periksa_usia(usia: int | None) -> list[Peringatan]:
        if usia is not None and usia < USIA_MINIMAL_DATA_LATIH:
            return [
                Peringatan(
                    field=None,
                    pesan=(
                        f"Pasien berusia {usia} tahun. Model dilatih dengan data pasien remaja dan dewasa, "
                        "jadi periksa ulang rekomendasi ini secara klinis."
                    ),
                )
            ]
        return []


def tanda_vital_triase(triase: Triase) -> TandaVital:
    return TandaVital.model_construct(**{kolom: getattr(triase, kolom) for kolom in KOLOM_TANDA_VITAL})


def peringatan_triase(triase: Triase) -> list[Peringatan]:
    """Peringatan tidak disimpan di basis data, jadi dihitung ulang dari tanda vital yang tersimpan."""
    pasien = triase.kunjungan.pasien
    usia = usia_pasien(pasien.tanggal_lahir, pasien.perkiraan_usia, triase.waktu_triase.astimezone(WIB).date())
    return PeringatanVital.periksa(tanda_vital_triase(triase)) + PeringatanVital.periksa_usia(usia)


class TriaseService:
    def __init__(self, registry: ModelRegistry, cache: CacheKonfigurasi) -> None:
        self.registry = registry
        self.cache = cache

    def buat(self, id_kunjungan: uuid.UUID, data: TriaseInput, perawat: Pengguna) -> Triase:
        try:
            triase = self._buat(id_kunjungan, data, perawat)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        db.session.refresh(triase)
        return triase

    def _buat(self, id_kunjungan: uuid.UUID, data: TriaseInput, perawat: Pengguna) -> Triase:
        # Baris kunjungan dikunci supaya dua triase yang dikirim bersamaan tidak sama-sama tercatat "awal".
        kunjungan = db.session.scalar(select(Kunjungan).where(Kunjungan.id_kunjungan == id_kunjungan).with_for_update())
        if kunjungan is None:
            raise TidakDitemukanError("Kunjungan tidak ditemukan.")
        if kunjungan.status != StatusKunjungan.MENUNGGU:
            raise KonflikError("Kunjungan ini sudah ditangani atau selesai, jadi tidak bisa ditriase lagi.")

        sudah_ditriase = db.session.scalar(select(exists().where(Triase.id_kunjungan == id_kunjungan)))
        pemindaian = self._ambil_pemindaian(data.id_pemindaian, perawat)

        pasien = kunjungan.pasien
        tv = data.tanda_vital
        fitur = FiturTriase(
            usia=usia_pasien(pasien.tanggal_lahir, pasien.perkiraan_usia, hari_ini()),
            jenis_kelamin=pasien.jenis_kelamin,
            kategori_keluhan=data.kategori_keluhan,
            tingkat_kesadaran=data.tingkat_kesadaran,
            skala_nyeri=data.skala_nyeri,
            td_sistolik=tv.td_sistolik,
            td_diastolik=tv.td_diastolik,
            nadi=tv.nadi,
            laju_napas=tv.laju_napas,
            suhu=tv.suhu,
            saturasi=tv.saturasi,
            gejala=data.gejala,
        )
        konfigurasi = self.cache.ambil()
        hasil = buat_klasifikator(self.registry.model_triase, konfigurasi.ambang_aturan).klasifikasi(fitur)

        triase = Triase(
            id_kunjungan=id_kunjungan,
            jenis=JenisTriase.ULANG if sudah_ditriase else JenisTriase.AWAL,
            dibuat_oleh=perawat.id_pengguna,
            keluhan_utama=data.keluhan_utama,
            gejala=data.gejala,
            kategori_keluhan=data.kategori_keluhan,
            skala_nyeri=data.skala_nyeri,
            tingkat_kesadaran=data.tingkat_kesadaran,
            **{kolom: getattr(tv, kolom) for kolom in KOLOM_TANDA_VITAL},
            sumber_tanda_vital=self._sumber_tanda_vital(pemindaian),
            risk_level=hasil.risk_level,
            sumber_rekomendasi=hasil.sumber,
            penjelasan_ai=hasil.penjelasan_json(),
        )
        db.session.add(triase)
        db.session.flush()
        self._konfirmasi_pemindaian(pemindaian, triase, tv)
        return triase

    @staticmethod
    def _ambil_pemindaian(daftar_id: list[uuid.UUID], perawat: Pengguna) -> list[PemindaianAlat]:
        """Pemindaian harus milik perawat yang sama dan belum dipakai triase lain (keputusan K17)."""
        if not daftar_id:
            return []
        # Satu kueri dengan urutan tetap, supaya dua triase bersamaan selalu mengunci baris dalam urutan yang sama.
        terkunci = db.session.scalars(
            select(PemindaianAlat)
            .where(PemindaianAlat.id_pemindaian.in_(daftar_id))
            .order_by(PemindaianAlat.id_pemindaian)
            .with_for_update()
        ).all()
        per_id = {p.id_pemindaian: p for p in terkunci}
        hasil = []
        galat = []
        for i, id_pemindaian in enumerate(daftar_id):
            pemindaian = per_id.get(id_pemindaian)
            if pemindaian is None or pemindaian.dipindai_oleh != perawat.id_pengguna:
                galat.append({"field": f"id_pemindaian.{i}", "pesan": "Hasil pemindaian tidak ditemukan."})
            elif pemindaian.id_triase is not None:
                pesan = "Hasil pemindaian ini sudah dipakai triase lain."
                galat.append({"field": f"id_pemindaian.{i}", "pesan": pesan})
            else:
                hasil.append(pemindaian)
        if galat:
            raise ValidasiGagalError(galat)
        return hasil

    @staticmethod
    def _kolom_terbaca(pemindaian: PemindaianAlat) -> set[str]:
        return {kolom for kolom in pemindaian.nilai_terbaca if kolom in KOLOM_TANDA_VITAL}

    def _sumber_tanda_vital(self, pemindaian: list[PemindaianAlat]) -> SumberTandaVital:
        if not pemindaian:
            return SumberTandaVital.MANUAL
        terbaca = set().union(*(self._kolom_terbaca(p) for p in pemindaian))
        return SumberTandaVital.PEMINDAIAN if terbaca >= set(KOLOM_TANDA_VITAL) else SumberTandaVital.CAMPURAN

    def _konfirmasi_pemindaian(self, pemindaian: list[PemindaianAlat], triase: Triase, tv: TandaVital) -> None:
        # Nilai yang akhirnya dikirim perawat disimpan sebagai bahan evaluasi akurasi pembaca layar (FR-09).
        for p in pemindaian:
            p.nilai_dikonfirmasi = {kolom: _nilai_json(getattr(tv, kolom)) for kolom in sorted(self._kolom_terbaca(p))}
            p.id_triase = triase.id_triase

    @staticmethod
    def ambil(id_triase: uuid.UUID) -> Triase:
        triase = db.session.get(Triase, id_triase)
        if triase is None:
            raise TidakDitemukanError("Triase tidak ditemukan.")
        return triase

    @staticmethod
    def catatan_validasi_terakhir(id_triase: uuid.UUID) -> str | None:
        return db.session.scalar(
            select(LogAudit.catatan)
            .where(LogAudit.id_triase == id_triase, LogAudit.aksi.in_((AksiAudit.KOREKSI, AksiAudit.AJUKAN_REVIEW)))
            .order_by(LogAudit.waktu.desc(), LogAudit.id_log.desc())
            .limit(1)
        )
