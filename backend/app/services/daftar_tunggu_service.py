"""Daftar tunggu dan penanda triase ulang (FR-07, Desain 2.7 dan Gambar 2.19-2.21).

Penanda dihitung saat request dibaca, jadi tidak ada penjadwal maupun pekerjaan latar.
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import aliased

from app.extensions import db
from app.models import Kunjungan, Pasien, Triase
from app.models.enums import RiskLevel, StatusKunjungan, StatusValidasi
from app.services.konfigurasi_service import NilaiKonfigurasi
from app.utils.waktu import WIB, usia_pasien

URUTAN_LEVEL = {RiskLevel.RENDAH: 0, RiskLevel.SEDANG: 1, RiskLevel.TINGGI: 2, RiskLevel.KRITIS: 3}
STATUS_BELUM_DIVALIDASI = (StatusValidasi.MENUNGGU, StatusValidasi.MENUNGGU_REVIEW_DOKTER)


@dataclass(frozen=True)
class ItemDaftarTunggu:
    kunjungan: Kunjungan
    pasien: Pasien
    triase_terakhir: Triase | None
    usia: int | None
    lama_menunggu: int
    batas_tunggu: int | None
    status_tanda: str

    @property
    def menunggu_validasi(self) -> bool:
        return self.triase_terakhir is not None and self.triase_terakhir.status_validasi in STATUS_BELUM_DIVALIDASI

    @property
    def review_diajukan(self) -> bool:
        return (
            self.triase_terakhir is not None
            and self.triase_terakhir.status_validasi == StatusValidasi.MENUNGGU_REVIEW_DOKTER
        )


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
        baris = db.session.execute(
            select(Kunjungan, Pasien, terakhir)
            .join(Pasien, Pasien.id_pasien == Kunjungan.id_pasien)
            .outerjoin(terakhir, terakhir.id_kunjungan == Kunjungan.id_kunjungan)
            .where(Kunjungan.status == StatusKunjungan.MENUNGGU)
        ).all()
        hari = sekarang.astimezone(WIB).date()
        items = [self._item(kunjungan, pasien, triase, sekarang, hari) for kunjungan, pasien, triase in baris]
        return sorted(items, key=self._kunci_urut)

    def _item(self, kunjungan: Kunjungan, pasien: Pasien, triase: Triase | None, sekarang: datetime, hari):
        acuan = kunjungan.waktu_datang if triase is None else triase.waktu_triase
        lama = max(0, int((sekarang - acuan).total_seconds() // 60))
        batas = None if triase is None else self.konfigurasi.batas_tunggu(triase.risk_level)
        if triase is None:
            tanda = "belum_ditriase"
        elif self.perlu_triase_ulang(lama, batas):
            tanda = "perlu_triase_ulang"
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
        )

    @staticmethod
    def perlu_triase_ulang(lama_menunggu: int, batas_tunggu: int | None) -> bool:
        """Lewat batas waktu tunggu level ini. Pasien kritis tidak punya batas karena harus segera ditangani.

        Pemicu kedua di Gambar 2.19, tanda vital baru masuk, tidak punya sumber data di ERD dan tidak
        dibuat (keputusan K11).
        """
        return batas_tunggu is not None and lama_menunggu > batas_tunggu

    @staticmethod
    def _kunci_urut(item: ItemDaftarTunggu) -> tuple:
        # Urutan Gambar 2.19: kritis, belum ditriase, lewat batas, level, lalu lama menunggu.
        level = item.triase_terakhir.risk_level if item.triase_terakhir is not None else None
        return (
            level != RiskLevel.KRITIS,
            item.status_tanda != "belum_ditriase",
            item.status_tanda != "perlu_triase_ulang",
            -URUTAN_LEVEL.get(level, -1),
            -item.lama_menunggu,
            item.kunjungan.waktu_datang,
            str(item.kunjungan.id_kunjungan),
        )
