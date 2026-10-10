"""Verifikasi JWT, pemuatan ulang pengguna di setiap request, dan RBAC tiga peran.

Semua error dari Flask-JWT-Extended diubah menjadi Problem Details 401 berbahasa Indonesia.
Bawaannya memakai 422 untuk token rusak, yang bisa tertukar dengan error validasi field.
"""

import uuid
from collections.abc import Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from flask import Response
from flask_jwt_extended import get_current_user, verify_jwt_in_request

from app.extensions import db, jwt
from app.models import Pengguna
from app.models.enums import Peran
from app.utils.errors import AplikasiError, Tipe, respons_problem

P = ParamSpec("P")
R = TypeVar("R")


class AksesDitolakError(AplikasiError):
    status = 403
    tipe = Tipe.AKSES_DITOLAK
    judul = "Akses ditolak"


@jwt.user_lookup_loader
def muat_pengguna(_header: dict[str, Any], data: dict[str, Any]) -> Pengguna | None:
    """Membaca ulang pengguna setiap request; akun yang dinonaktifkan langsung kehilangan akses."""
    try:
        id_pengguna = uuid.UUID(str(data["sub"]))
    except (KeyError, ValueError):
        return None
    pengguna = db.session.get(Pengguna, id_pengguna)
    if pengguna is None or not pengguna.is_active:
        return None
    return pengguna


@jwt.user_lookup_error_loader
def _pengguna_tidak_valid(_header: dict[str, Any], _data: dict[str, Any]) -> Response:
    return respons_problem(
        401, Tipe.SESI_BERAKHIR, "Sesi berakhir", "Akun tidak aktif atau tidak ditemukan. Silakan masuk kembali."
    )


@jwt.unauthorized_loader
def _tanpa_token(alasan: str) -> Response:
    if "CSRF" in alasan:
        return respons_problem(
            401, Tipe.TIDAK_TERAUTENTIKASI, "Token CSRF tidak valid", "Header X-CSRF-TOKEN tidak ada atau tidak cocok."
        )
    return respons_problem(401, Tipe.TIDAK_TERAUTENTIKASI, "Belum masuk", "Silakan masuk terlebih dahulu.")


@jwt.invalid_token_loader
def _token_tidak_valid(alasan: str) -> Response:
    if "refresh tokens" in alasan:
        detail = "Jenis token tidak sesuai untuk alamat ini."
    else:
        detail = "Token tidak dapat dibaca. Silakan masuk kembali."
    return respons_problem(401, Tipe.TOKEN_TIDAK_VALID, "Token tidak valid", detail)


@jwt.expired_token_loader
def _token_kedaluwarsa(_header: dict[str, Any], data: dict[str, Any]) -> Response:
    if data.get("type") == "refresh":
        # Refresh token habis (8 jam): klien harus login ulang.
        return respons_problem(401, Tipe.SESI_BERAKHIR, "Sesi berakhir", "Sesi telah berakhir. Silakan masuk kembali.")
    # Access token habis (15 menit): klien cukup memanggil /api/v1/auth/refresh.
    return respons_problem(
        401, Tipe.TOKEN_KEDALUWARSA, "Token kedaluwarsa", "Perbarui token lewat /api/v1/auth/refresh."
    )


@jwt.revoked_token_loader
def _token_dicabut(_header: dict[str, Any], _data: dict[str, Any]) -> Response:
    return respons_problem(401, Tipe.SESI_BERAKHIR, "Sesi berakhir", "Sesi telah berakhir. Silakan masuk kembali.")


@jwt.needs_fresh_token_loader
def _perlu_token_baru(_header: dict[str, Any], _data: dict[str, Any]) -> Response:
    return respons_problem(401, Tipe.TIDAK_TERAUTENTIKASI, "Perlu masuk ulang", "Silakan masuk kembali.")


@jwt.token_verification_failed_loader
def _verifikasi_token_gagal(_header: dict[str, Any], _data: dict[str, Any]) -> Response:
    return respons_problem(401, Tipe.TOKEN_TIDAK_VALID, "Token tidak valid", "Silakan masuk kembali.")


def role_required(*peran_diizinkan: Peran) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Membatasi endpoint untuk peran tertentu. Peran dibaca dari basis data, bukan dari klaim token.

    Pasang tepat di bawah dekorator rute (@bp.get/@bp.post). Bila dipasang di atasnya,
    pemeriksaan ini tidak ikut terdaftar dan endpoint menjadi terbuka.
    """
    if not peran_diizinkan:
        raise ValueError("role_required membutuhkan minimal satu peran.")

    def dekorator(fungsi: Callable[P, R]) -> Callable[P, R]:
        @wraps(fungsi)
        def pembungkus(*args: P.args, **kwargs: P.kwargs) -> R:
            verify_jwt_in_request()
            pengguna: Pengguna = get_current_user()
            if pengguna.peran not in peran_diizinkan:
                raise AksesDitolakError("Peran Anda tidak memiliki akses ke fitur ini.")
            return fungsi(*args, **kwargs)

        return pembungkus

    return dekorator
