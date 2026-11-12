from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db

# Nilai bawaan baris konfigurasi setelah migrasi ICU (0002). Ambang adalah skor NEWS2 (7 respons darurat,
# 5 respons segera, 3 perlu perhatian). Batas tunggu dipakai sebagai interval observasi per level, dalam menit.
KONFIGURASI_BAWAAN = {
    "id_konfigurasi": 1,
    "versi_model": "rf-icu-physionet2019-v1",
    "ambang_kritis": 7,
    "ambang_tinggi": 5,
    "ambang_sedang": 3,
    "batas_tunggu_kritis": 15,
    "batas_tunggu_tinggi": 30,
    "batas_tunggu_sedang": 60,
    "batas_tunggu_rendah": 120,
    "ambang_keyakinan": Decimal("0.85"),
}


class Konfigurasi(db.Model):
    """Pengaturan global penilaian prioritas ICU. Hanya ada satu baris (id_konfigurasi = 1)."""

    __tablename__ = "konfigurasi"
    __table_args__ = (
        sa.CheckConstraint("id_konfigurasi = 1", name="ck_konfigurasi_satu_baris"),
        sa.CheckConstraint(
            "ambang_kritis > ambang_tinggi AND ambang_tinggi > ambang_sedang AND ambang_sedang > 0",
            name="ck_konfigurasi_ambang_berurutan",
        ),
        sa.CheckConstraint(
            "batas_tunggu_kritis > 0 AND batas_tunggu_kritis <= batas_tunggu_tinggi "
            "AND batas_tunggu_tinggi <= batas_tunggu_sedang AND batas_tunggu_sedang <= batas_tunggu_rendah",
            name="ck_konfigurasi_batas_tunggu",
        ),
        sa.CheckConstraint("ambang_keyakinan BETWEEN 0 AND 1", name="ck_konfigurasi_ambang_keyakinan"),
    )

    id_konfigurasi: Mapped[int] = mapped_column(sa.SmallInteger, primary_key=True, autoincrement=False)
    versi_model: Mapped[str] = mapped_column(sa.String(50))
    ambang_kritis: Mapped[int] = mapped_column(sa.SmallInteger)
    ambang_tinggi: Mapped[int] = mapped_column(sa.SmallInteger)
    ambang_sedang: Mapped[int] = mapped_column(sa.SmallInteger)
    # Interval observasi dalam menit, per risk level (FR-07).
    batas_tunggu_kritis: Mapped[int] = mapped_column(sa.SmallInteger)
    batas_tunggu_tinggi: Mapped[int] = mapped_column(sa.SmallInteger)
    batas_tunggu_sedang: Mapped[int] = mapped_column(sa.SmallInteger)
    batas_tunggu_rendah: Mapped[int] = mapped_column(sa.SmallInteger)
    ambang_keyakinan: Mapped[Decimal] = mapped_column(sa.Numeric(3, 2))
