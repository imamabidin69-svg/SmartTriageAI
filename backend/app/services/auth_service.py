"""Logika login dan pembuatan token (FR-01)."""

import secrets
from functools import cache

from flask_jwt_extended import create_access_token, create_refresh_token
from sqlalchemy import select
from sqlalchemy.orm import Session, scoped_session
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models import Pengguna
from app.utils.errors import AplikasiError, Tipe


class KredensialSalahError(AplikasiError):
    status = 401
    tipe = Tipe.KREDENSIAL_SALAH
    judul = "Email atau password salah"


class AkunNonaktifError(AplikasiError):
    status = 403
    tipe = Tipe.AKUN_NONAKTIF
    judul = "Akun tidak aktif"


@cache
def _hash_pembanding() -> str:
    """Hash acak untuk email yang tidak terdaftar, supaya waktu respons login selalu sama."""
    return generate_password_hash(secrets.token_urlsafe(32), method="scrypt")


class AuthService:
    def __init__(self, sesi: Session | scoped_session | None = None) -> None:
        self.sesi = sesi if sesi is not None else db.session

    def login(self, email: str, password: str) -> Pengguna:
        """Mengembalikan pengguna bila password cocok dan akun aktif.

        Status akun baru diperiksa setelah password cocok, sehingga pesan "akun tidak aktif"
        hanya terlihat oleh orang yang mengetahui password-nya (SKPL TC-03).
        """
        pengguna = self.sesi.scalar(select(Pengguna).where(Pengguna.email == email))
        if pengguna is None:
            check_password_hash(_hash_pembanding(), password)
            raise KredensialSalahError("Periksa kembali email dan password Anda.")
        if not pengguna.cek_password(password):
            raise KredensialSalahError("Periksa kembali email dan password Anda.")
        if not pengguna.is_active:
            raise AkunNonaktifError("Akun ini sudah dinonaktifkan. Hubungi admin IGD.")
        return pengguna

    @staticmethod
    def buat_access_token(pengguna: Pengguna) -> str:
        # Peran selalu dibaca dari basis data saat token dibuat, termasuk saat refresh.
        return create_access_token(identity=str(pengguna.id_pengguna), additional_claims={"role": pengguna.peran.value})

    @staticmethod
    def buat_refresh_token(pengguna: Pengguna) -> str:
        return create_refresh_token(identity=str(pengguna.id_pengguna))
