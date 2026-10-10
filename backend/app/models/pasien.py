import uuid
from datetime import date, datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.enums import JENIS_KELAMIN, JenisKelamin


class Pasien(db.Model):
    """Identitas minimal pasien yang didaftarkan perawat (FR-02)."""

    __tablename__ = "pasien"
    __table_args__ = (
        # NIK unik bila diisi (Desain Bab 5).
        sa.Index("uq_pasien_nik", "nik", unique=True, postgresql_where=sa.text("nik IS NOT NULL")),
        sa.CheckConstraint("nik IS NULL OR nik ~ '^[0-9]{16}$'", name="ck_pasien_nik_format"),
        # FR-02: tanggal lahir atau perkiraan usia, salah satu wajib ada.
        sa.CheckConstraint(
            "tanggal_lahir IS NOT NULL OR perkiraan_usia IS NOT NULL", name="ck_pasien_tanggal_lahir_atau_usia"
        ),
        sa.CheckConstraint(
            "perkiraan_usia IS NULL OR perkiraan_usia BETWEEN 0 AND 150", name="ck_pasien_perkiraan_usia"
        ),
    )

    id_pasien: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()"))
    didaftarkan_oleh: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("pengguna.id_pengguna"))
    nama: Mapped[str] = mapped_column(sa.String(120))
    tanggal_lahir: Mapped[date | None]
    perkiraan_usia: Mapped[int | None] = mapped_column(sa.SmallInteger)
    jenis_kelamin: Mapped[JenisKelamin] = mapped_column(JENIS_KELAMIN)
    nik: Mapped[str | None] = mapped_column(sa.CHAR(16))
    no_telepon: Mapped[str | None] = mapped_column(sa.String(20))
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())

    pendaftar = relationship("Pengguna")
    kunjungan = relationship("Kunjungan", back_populates="pasien")
