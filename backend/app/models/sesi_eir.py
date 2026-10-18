import uuid
from datetime import UTC, datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.enums import PENGISI_EIR, STATUS_SESI_EIR, PengisiEir, StatusSesiEir

PERAN_EIR = "eir"
PERAN_PENGISI = "pengisi"


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

    @property
    def berjalan(self) -> bool:
        return self.status == StatusSesiEir.BERJALAN

    @property
    def jumlah_jawaban(self) -> int:
        return sum(1 for item in self.transkrip or [] if item["peran"] == PERAN_PENGISI)

    def tambah_pesan(self, peran: str, teks: str, waktu: datetime) -> None:
        # List baru supaya SQLAlchemy mendeteksi perubahan kolom JSONB. Waktu disimpan dalam UTC seperti
        # kolom timestamptz lain yang dibaca dari basis data.
        item = {"peran": peran, "teks": teks, "waktu": waktu.astimezone(UTC).isoformat()}
        self.transkrip = [*(self.transkrip or []), item]

    def hentikan(self, alasan: str, waktu: datetime) -> None:
        """Sesi dihentikan karena tanda bahaya; peringatan muncul di GET /peringatan."""
        self.status = StatusSesiEir.DIHENTIKAN
        self.tanda_bahaya = alasan
        self.waktu_selesai = waktu

    def selesaikan(self, ringkasan: dict[str, Any], waktu: datetime) -> None:
        self.status = StatusSesiEir.SELESAI
        self.ringkasan = ringkasan
        self.waktu_selesai = waktu
