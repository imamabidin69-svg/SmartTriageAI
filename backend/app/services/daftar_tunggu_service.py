"""Papan prioritas ICU dan penanda observasi terlambat (FR-07, Desain 2.7 dan Gambar 2.19-2.21).

Daftar berisi semua pasien yang belum keluar ICU, diurutkan menurut siapa yang harus ditangani lebih dulu.
Penanda dihitung saat request dibaca, jadi tidak ada penjadwal maupun pekerjaan latar. Penanda "Ringkasan Eir
siap" (mockup SKPL Gambar 7.1, keputusan M4) juga dihitung di sini.
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import aliased

from app.extensions import db
from app.models import Kunjungan, Pasien, SesiEir, Triase
from app.models.enums import RiskLevel, StatusKunjungan, StatusSesiEir, StatusValidasi
from app.services.konfigurasi_service import NilaiKonfigurasi
from app.utils.waktu import WIB, usia_pasien

URUTAN_LEVEL = {RiskLevel.RENDAH: 0, RiskLevel.SEDANG: 1, RiskLevel.TINGGI: 2, RiskLevel.KRITIS: 3}
STATUS_BELUM_DIVALIDASI = (StatusValidasi.MENUNGGU, StatusValidasi.MENUNGGU_REVIEW_DOKTER)
# Pasien yang masih di ICU: dirawat (menunggu) atau sedang menjalani tindakan/operasi (ditangani).
STATUS_DI_ICU = (StatusKunjungan.MENUNGGU, StatusKunjungan.DITANGANI)


@dataclass(frozen=True)
class ItemDaftarTunggu:
    kunjungan: Kunjungan
    pasien: Pasien
    triase_terakhir: Triase | None
    usia: int | None
    lama_menunggu: int
    batas_tunggu: int | None
    status_tanda: str
    ringkasan_eir_siap: bool = False

    @property
    def menunggu_validasi(self) -> bool:
        return self.triase_terakhir is not None and self.triase_terakhir.status_validasi in STATUS_BELUM_DIVALIDASI

    @property
    def review_diajukan(self) -> bool:
        return (
            self.triase_terakhir is not None
            and self.triase_terakhir.status_validasi == StatusValidasi.MENUNGGU_REVIEW_DOKTER
        )


def sesi_eir_terakhir_per_kunjungan():
    """Satu sesi Eir terbaru untuk setiap kunjungan, dengan urutan yang sama seperti GET /ringkasan-eir."""
    return (
        select(SesiEir)
        .distinct(SesiEir.id_kunjungan)
        .order_by(SesiEir.id_kunjungan, SesiEir.waktu_persetujuan.desc(), SesiEir.id_sesi.desc())
        .subquery()
    )


def ringkasan_eir_siap(sesi: SesiEir | None, triase: Triase | None) -> bool:
    """Sesi terakhir selesai dengan ringkasan dan belum ada triase sesudahnya. Setelah perawat melakukan triase
    ulang, ringkasan itu dianggap sudah dipakai sehingga penandanya hilang."""
    if sesi is None or sesi.status != StatusSesiEir.SELESAI or not sesi.ringkasan or sesi.waktu_selesai is None:
        return False
    return triase is None or sesi.waktu_selesai > triase.waktu_triase


def triase_terakhir_per_kunjungan():
    """Satu triase terbaru untuk setiap kunjungan (DISTINCT ON, memakai idx_triase_kunjungan)."""
    return (
        select(Triase)
        .distinct(Triase.id_kunjungan)
        .order_by(Triase.id_kunjungan, Triase.waktu_triase.desc(), Triase.id_triase.desc())
        .subquery()
    )


class DaftarTungguService:
    def __init__(self, konfigurasi: NilaiKonfigurasi) -> None:
        self.konfigurasi = konfigurasi

    def susun(self, sekarang: datetime) -> list[ItemDaftarTunggu]:
        terakhir = aliased(Triase, triase_terakhir_per_kunjungan())
        sesi_terakhir = aliased(SesiEir, sesi_eir_terakhir_per_kunjungan())
        baris = db.session.execute(
            select(Kunjungan, Pasien, terakhir, sesi_terakhir)
            .join(Pasien, Pasien.id_pasien == Kunjungan.id_pasien)
            .outerjoin(terakhir, terakhir.id_kunjungan == Kunjungan.id_kunjungan)
            .outerjoin(sesi_terakhir, sesi_terakhir.id_kunjungan == Kunjungan.id_kunjungan)
            .where(Kunjungan.status.in_(STATUS_DI_ICU))
        ).all()
        hari = sekarang.astimezone(WIB).date()
        items = [
            self._item(kunjungan, pasien, triase, sekarang, hari, ringkasan_eir_siap(sesi, triase))
            for kunjungan, pasien, triase, sesi in baris
        ]
        return sorted(items, key=self._kunci_urut)

    def _item(
        self,
        kunjungan: Kunjungan,
        pasien: Pasien,
        triase: Triase | None,
        sekarang: datetime,
        hari,
        eir_siap: bool = False,
    ):
        acuan = kunjungan.waktu_datang if triase is None else triase.waktu_triase
        lama = max(0, int((sekarang - acuan).total_seconds() // 60))
        batas = None if triase is None else self.konfigurasi.batas_tunggu(triase.risk_level)
        if triase is None:
            tanda = "belum_dinilai"
        elif self.observasi_terlambat(lama, batas):
            tanda = "observasi_terlambat"
        else:
            tanda = "normal"
        return ItemDaftarTunggu(
            kunjungan=kunjungan,
            pasien=pasien,
            triase_terakhir=triase,
            usia=usia_pasien(pasien.tanggal_lahir, pasien.perkiraan_usia, hari),
            lama_menunggu=lama,
            batas_tunggu=batas,
            status_tanda=tanda,
            ringkasan_eir_siap=eir_siap,
        )

    @staticmethod
    def observasi_terlambat(lama: int, interval: int | None) -> bool:
        """Observasi terakhir sudah lebih lama dari interval observasi untuk level pasien ini."""
        return interval is not None and lama > interval

    @staticmethod
    def _kunci_urut(item: ItemDaftarTunggu) -> tuple:
        """Urutan prioritas penanganan di ICU.

        1. Pasien yang sedang menjalani tindakan atau operasi ditaruh paling bawah karena sudah ditangani.
        2. Level: Kritis, lalu pasien yang belum dinilai (harus segera dinilai), lalu Tinggi, Sedang, Rendah.
        3. Di level yang sama: yang menunggu persetujuan dokter, lalu yang observasinya terlambat.
        4. Lalu peluang perburukan dan skor NEWS2 yang lebih tinggi, lalu yang paling lama sejak observasi.
        """
        triase = item.triase_terakhir
        if triase is None:
            peringkat_level = 1
        else:
            peringkat_level = {RiskLevel.KRITIS: 0, RiskLevel.TINGGI: 2, RiskLevel.SEDANG: 3, RiskLevel.RENDAH: 4}[
                triase.risk_level
            ]
        peluang = float(triase.peluang_perburukan) if triase is not None and triase.peluang_perburukan else 0.0
        skor = triase.skor_news2 if triase is not None else 0
        return (
            item.kunjungan.status == StatusKunjungan.DITANGANI,
            peringkat_level,
            not item.menunggu_validasi,
            item.status_tanda != "observasi_terlambat",
            -peluang,
            -skor,
            -item.lama_menunggu,
            item.kunjungan.waktu_datang,
            str(item.kunjungan.id_kunjungan),
        )
