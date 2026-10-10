import uuid
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.enums import PENGISI_EIR, STATUS_SESI_EIR, PengisiEir, StatusSesiEir


class SesiEir(db.Model):
    """Percakapan anamnesis Eir untuk pasien zona hijau atau keluarganya (FR-08)."""

    __tablename__ = "sesi_eir"

    id_sesi: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()"))
    id_kunjungan: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("kunjungan.id_kunjungan"))
    pengisi: Mapped[PengisiEir] = mapped_column(PENGISI_EIR)
    waktu_persetujuan: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True))
    status: Mapped[StatusSesiEir] = mapped_column(STATUS_SESI_EIR, server_default=StatusSesiEir.BERJALAN.value)
    tanda_bahaya: Mapped[str | None] = mapped_column(sa.Text)
    transkrip: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, server_default=sa.text("'[]'::jsonb"))
    ringkasan: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    waktu_selesai: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))

    kunjungan = relationship("Kunjungan", back_populates="sesi_eir")
