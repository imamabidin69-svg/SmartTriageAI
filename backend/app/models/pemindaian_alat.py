import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.enums import JENIS_ALAT, JenisAlat


class PemindaianAlat(db.Model):
    """Hasil baca YOLO dari foto layar alat dan nilai yang dikonfirmasi perawat. Fotonya tidak disimpan."""

    __tablename__ = "pemindaian_alat"
    __table_args__ = (sa.CheckConstraint("keyakinan BETWEEN 0 AND 1", name="ck_pemindaian_alat_keyakinan"),)

    id_pemindaian: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()")
    )
    # Masih kosong sampai perawat mengirim form triase yang memakai hasil pemindaian ini.
    id_triase: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("triase.id_triase"))
    dipindai_oleh: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("pengguna.id_pengguna"))
    jenis_alat: Mapped[JenisAlat] = mapped_column(JENIS_ALAT)
    nilai_terbaca: Mapped[dict[str, Any]] = mapped_column(JSONB)
    nilai_dikonfirmasi: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    keyakinan: Mapped[Decimal] = mapped_column(sa.Numeric(4, 3))
    waktu: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())

    triase = relationship("Triase", back_populates="pemindaian")
    pemindai = relationship("Pengguna")
