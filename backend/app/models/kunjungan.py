import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.enums import STATUS_KUNJUNGAN, StatusKunjungan


class Kunjungan(db.Model):
    """Satu kedatangan pasien ke IGD beserta status menunggunya (FR-02, FR-07)."""

    __tablename__ = "kunjungan"
    __table_args__ = (
        # Daftar tunggu (FR-07, NFR-02) dan riwayat pasien (FR-09), sesuai Desain Bab 5.
        sa.Index("idx_kunjungan_status", "status", "waktu_datang"),
        sa.Index("idx_kunjungan_pasien", "id_pasien", sa.text("waktu_datang DESC")),
    )

    id_kunjungan: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()")
    )
    id_pasien: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("pasien.id_pasien"))
    waktu_datang: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())
    waktu_ditangani: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    status: Mapped[StatusKunjungan] = mapped_column(STATUS_KUNJUNGAN, server_default=StatusKunjungan.MENUNGGU.value)

    pasien = relationship("Pasien", back_populates="kunjungan")
    triase = relationship("Triase", back_populates="kunjungan")
    sesi_eir = relationship("SesiEir", back_populates="kunjungan")
