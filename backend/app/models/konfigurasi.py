from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db

# Nilai bawaan baris konfigurasi yang disisipkan migrasi awal. Ambang aturan cadangan diambil
# dari prototipe (ai-config-store.ts), batas tunggu dan ambang keyakinan dari Desain 2.4 dan 2.7.
KONFIGURASI_BAWAAN = {
    "id_konfigurasi": 1,
    "versi_model": "smarttriage-rf-v1.0.0",
    "ambang_kritis": 6,
    "ambang_tinggi": 4,
    "ambang_sedang": 2,
    "batas_tunggu_tinggi": 10,
    "batas_tunggu_sedang": 30,
    "batas_tunggu_rendah": 60,
    "ambang_keyakinan": Decimal("0.85"),
}


class Konfigurasi(db.Model):
    """Pengaturan global triase. Hanya ada satu baris (id_konfigurasi = 1)."""

    __tablename__ = "konfigurasi"
    __table_args__ = (
        sa.CheckConstraint("id_konfigurasi = 1", name="ck_konfigurasi_satu_baris"),
        sa.CheckConstraint(
            "ambang_kritis > ambang_tinggi AND ambang_tinggi > ambang_sedang AND ambang_sedang > 0",
            name="ck_konfigurasi_ambang_berurutan",
        ),
        sa.CheckConstraint(
            "batas_tunggu_tinggi > 0 AND batas_tunggu_tinggi <= batas_tunggu_sedang "
            "AND batas_tunggu_sedang <= batas_tunggu_rendah",
            name="ck_konfigurasi_batas_tunggu",
        ),
        sa.CheckConstraint("ambang_keyakinan BETWEEN 0 AND 1", name="ck_konfigurasi_ambang_keyakinan"),
    )

    id_konfigurasi: Mapped[int] = mapped_column(sa.SmallInteger, primary_key=True, autoincrement=False)
    versi_model: Mapped[str] = mapped_column(sa.String(50))
    ambang_kritis: Mapped[int] = mapped_column(sa.SmallInteger)
    ambang_tinggi: Mapped[int] = mapped_column(sa.SmallInteger)
    ambang_sedang: Mapped[int] = mapped_column(sa.SmallInteger)
    # Dalam menit, per risk level (FR-07).
    batas_tunggu_tinggi: Mapped[int] = mapped_column(sa.SmallInteger)
    batas_tunggu_sedang: Mapped[int] = mapped_column(sa.SmallInteger)
    batas_tunggu_rendah: Mapped[int] = mapped_column(sa.SmallInteger)
    ambang_keyakinan: Mapped[Decimal] = mapped_column(sa.Numeric(3, 2))
