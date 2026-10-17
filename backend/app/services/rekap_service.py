"""Rekap evaluasi untuk admin dan ekspor CSV (FR-09, Desain 2.9 dan Gambar 2.25-2.27, keputusan K12, V1, V2, D8)."""

import csv
import io
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from sqlalchemy import case, func, select
from sqlalchemy.orm import aliased

from app.extensions import db
from app.models import Kunjungan, PemindaianAlat, Triase
from app.models.enums import JenisTriase, RiskLevel, StatusValidasi
from app.services.daftar_tunggu_service import triase_terakhir_per_kunjungan
from app.utils.errors import ValidasiGagalError
from app.utils.waktu import WIB, hari_ini

RENTANG_BAWAAN_HARI = 7
RENTANG_MAKSIMUM_HARI = 366


@dataclass(frozen=True)
class Rekap:
    dari: date
    sampai: date
    total_triase: int
    per_level: dict[RiskLevel, int]
    rata_tunggu_menit: dict[RiskLevel, float | None]
    persen_koreksi: float | None
    triase_ulang: int
    akurasi_pemindaian: float | None


def rentang_tanggal(dari: date | None, sampai: date | None) -> tuple[date, date]:
    """Bawaan tujuh hari terakhir sampai hari ini (WIB). Kedua ujung ikut dihitung."""
    sampai = sampai or hari_ini()
    dari = dari or sampai - timedelta(days=RENTANG_BAWAAN_HARI - 1)
    if dari > sampai:
        raise ValidasiGagalError([{"field": "dari", "pesan": "Tanggal awal tidak boleh melewati tanggal akhir."}])
    if (sampai - dari).days + 1 > RENTANG_MAKSIMUM_HARI:
        pesan = f"Rentang tanggal maksimal {RENTANG_MAKSIMUM_HARI} hari."
        raise ValidasiGagalError([{"field": "sampai", "pesan": pesan}])
    return dari, sampai


def batas_waktu(dari: date, sampai: date) -> tuple[datetime, datetime]:
    """Awal hari `dari` sampai awal hari setelah `sampai`, dalam WIB."""
    return datetime.combine(dari, time.min, WIB), datetime.combine(sampai + timedelta(days=1), time.min, WIB)


class RekapService:
    def hitung(self, dari: date, sampai: date) -> Rekap:
        mulai, akhir = batas_waktu(dari, sampai)
        dalam_rentang = (Triase.waktu_triase >= mulai, Triase.waktu_triase < akhir)

        per_level = dict.fromkeys(RiskLevel, 0)
        for level, jumlah in db.session.execute(
            select(Triase.risk_level, func.count()).where(*dalam_rentang).group_by(Triase.risk_level)
        ):
            per_level[level] = jumlah
        total = sum(per_level.values())

        dikoreksi, ulang = db.session.execute(
            select(
                func.count(case((Triase.status_validasi == StatusValidasi.DIKOREKSI, 1))),
                func.count(case((Triase.jenis == JenisTriase.ULANG, 1))),
            ).where(*dalam_rentang)
        ).one()

        return Rekap(
            dari=dari,
            sampai=sampai,
            total_triase=total,
            per_level=per_level,
            rata_tunggu_menit=self._rata_tunggu(mulai, akhir),
            persen_koreksi=round(dikoreksi / total * 100, 1) if total else None,
            triase_ulang=ulang,
            akurasi_pemindaian=self.akurasi_pemindaian(dari, sampai),
        )

    @staticmethod
    def _rata_tunggu(mulai: datetime, akhir: datetime) -> dict[RiskLevel, float | None]:
        """Keputusan V1: menit dari datang sampai ditangani, menurut level triase terakhir kunjungan.

        Hanya kunjungan yang datang dalam rentang dan sudah ditangani dokter.
        """
        terakhir = aliased(Triase, triase_terakhir_per_kunjungan())
        menit = func.extract("epoch", Kunjungan.waktu_ditangani - Kunjungan.waktu_datang) / 60
        hasil = dict.fromkeys(RiskLevel)
        for level, rata in db.session.execute(
            select(terakhir.risk_level, func.avg(menit))
            .join(terakhir, terakhir.id_kunjungan == Kunjungan.id_kunjungan)
            .where(
                Kunjungan.waktu_ditangani.is_not(None),
                Kunjungan.waktu_datang >= mulai,
                Kunjungan.waktu_datang < akhir,
            )
            .group_by(terakhir.risk_level)
        ):
            hasil[level] = round(float(rata), 1)
        return hasil

    @staticmethod
    def akurasi_pemindaian(dari: date, sampai: date) -> float | None:
        """Keputusan P6: kolom yang nilai terbacanya sama persis dengan nilai yang dikonfirmasi perawat,
        dibagi semua kolom terbaca. Hanya pemindaian yang sudah dipakai triase dalam rentang tanggal."""
        mulai, akhir = batas_waktu(dari, sampai)
        baris = db.session.execute(
            select(PemindaianAlat.nilai_terbaca, PemindaianAlat.nilai_dikonfirmasi)
            .join(Triase, Triase.id_triase == PemindaianAlat.id_triase)
            .where(
                PemindaianAlat.nilai_dikonfirmasi.is_not(None),
                Triase.waktu_triase >= mulai,
                Triase.waktu_triase < akhir,
            )
        ).all()
        total = benar = 0
        for terbaca, dikonfirmasi in baris:
            for kolom, nilai in terbaca.items():
                total += 1
                benar += dikonfirmasi.get(kolom) == nilai
        return round(benar / total * 100, 1) if total else None


# ---------------------------------------------------------------- CSV

PEMISAH_CSV = ";"  # Keputusan V2: langsung terbaca per kolom di Excel berpengaturan Indonesia.
AWALAN_FORMULA = ("=", "+", "-", "@", "\t", "\r")


def _angka(nilai: float | int | None) -> str:
    if nilai is None:
        return ""  # Sel kosong: belum ada data untuk dihitung.
    # Desimal ditulis dengan koma, pasangan pemisah titik koma di Excel berpengaturan Indonesia.
    return str(nilai).replace(".", ",")


def _aman(sel: str) -> str:
    """Sel yang diawali karakter formula diberi tanda petik supaya tidak dijalankan Excel."""
    return "'" + sel if sel.startswith(AWALAN_FORMULA) else sel


class PenulisCsv:
    def baris(self, rekap: Rekap) -> list[tuple[str, str]]:
        hasil = [
            ("Rentang tanggal", f"{rekap.dari.isoformat()} s.d. {rekap.sampai.isoformat()}"),
            ("Total triase", _angka(rekap.total_triase)),
        ]
        hasil += [(f"Triase {level.value}", _angka(rekap.per_level[level])) for level in RiskLevel]
        hasil += [
            (f"Rata-rata tunggu {level.value} (menit)", _angka(rekap.rata_tunggu_menit[level])) for level in RiskLevel
        ]
        hasil += [
            ("Persen koreksi dokter (%)", _angka(rekap.persen_koreksi)),
            ("Triase ulang", _angka(rekap.triase_ulang)),
            ("Akurasi pemindaian (%)", _angka(rekap.akurasi_pemindaian)),
        ]
        return hasil

    def stream(self, rekap: Rekap) -> Iterator[str]:
        """Baris CSV satu per satu, diawali BOM supaya Excel membaca UTF-8."""
        yield "﻿"
        for sel in [("metrik", "nilai"), *self.baris(rekap)]:
            buffer = io.StringIO()
            csv.writer(buffer, delimiter=PEMISAH_CSV, lineterminator="\r\n").writerow([_aman(s) for s in sel])
            yield buffer.getvalue()
