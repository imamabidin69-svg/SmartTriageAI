import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models.enums import PERAN, Peran


class Pengguna(db.Model):
    """Akun staf IGD dengan tiga peran: perawat, dokter, dan admin."""

    __tablename__ = "pengguna"
    __table_args__ = (
        # Email selalu disimpan huruf kecil supaya pencarian dan keunikan tidak peka kapital.
        sa.CheckConstraint("email = lower(email)", name="ck_pengguna_email_huruf_kecil"),
    )

    id_pengguna: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()")
    )
    nama: Mapped[str] = mapped_column(sa.String(120))
    email: Mapped[str] = mapped_column(sa.String(150), unique=True)
    password_hash: Mapped[str] = mapped_column(sa.String(255))
    peran: Mapped[Peran] = mapped_column(PERAN)
    is_active: Mapped[bool] = mapped_column(server_default=sa.true())
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())

    def atur_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password, method="scrypt")

    def cek_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<Pengguna {self.email} ({self.peran})>"
