import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.enums import AKSI_AUDIT, RISK_LEVEL, AksiAudit, RiskLevel


class LogAudit(db.Model):
    """Jejak keputusan klinis dan perubahan pengaturan.

    Tabel ini append-only: role aplikasi hanya diberi hak SELECT dan INSERT (lihat migrasi awal),
    dan foreign key-nya tidak memakai ON DELETE CASCADE supaya baris audit tidak ikut terhapus.
    """

    __tablename__ = "log_audit"
    __table_args__ = (
        # NFR-06: koreksi dan ajuan review wajib beralasan minimal 5 karakter. coalesce dipakai karena
        # length(NULL) bernilai NULL, dan CHECK yang bernilai NULL dianggap lolos.
        sa.CheckConstraint(
            "aksi NOT IN ('koreksi', 'ajukan_review') OR coalesce(char_length(btrim(catatan)), 0) >= 5",
            name="ck_alasan",
        ),
    )

    id_log: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()"))
    id_aktor: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("pengguna.id_pengguna"))
    id_triase: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("triase.id_triase"))
    aksi: Mapped[AksiAudit] = mapped_column(AKSI_AUDIT)
    catatan: Mapped[str | None] = mapped_column(sa.Text)
    level_sebelum: Mapped[RiskLevel | None] = mapped_column(RISK_LEVEL)
    level_sesudah: Mapped[RiskLevel | None] = mapped_column(RISK_LEVEL)
    waktu: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())

    aktor = relationship("Pengguna")
    triase = relationship("Triase")
