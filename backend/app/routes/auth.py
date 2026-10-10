"""Blueprint autentikasi: login, refresh, logout, dan profil (FR-01).

Web admin menerima token sebagai cookie HttpOnly dengan perlindungan CSRF. Aplikasi Flutter
mengirim header X-Client: mobile saat login dan menerima token di body, lalu memakai header
Authorization: Bearer. Refresh dan logout membalas lewat kanal yang sama dengan token yang dikirim.
"""

from flask import Response, current_app, jsonify, request
from flask_jwt_extended import (
    get_current_user,
    get_jwt_request_location,
    jwt_required,
    set_access_cookies,
    set_refresh_cookies,
    unset_jwt_cookies,
)
from flask_limiter.util import get_remote_address
from flask_openapi3 import APIBlueprint, Tag, validate_request

from app.extensions import limiter
from app.models import Pengguna
from app.routes.dokumen import RESPONS_422, SEMUA_KANAL_ACCESS, SEMUA_KANAL_REFRESH, respons_problem_doc
from app.services.auth_service import AuthService
from app.utils.schemas import (
    PANJANG_MAKS_EMAIL,
    LoginHeader,
    LoginRequest,
    PenggunaResponse,
    SesiResponse,
    normalisasi_email,
)

auth_bp = APIBlueprint(
    "auth", __name__, url_prefix="/auth", abp_tags=[Tag(name="Autentikasi")], abp_responses=RESPONS_422
)


def _batas_login() -> str:
    return current_app.config["BATAS_LOGIN"]


def _login_gagal(respons: Response) -> bool:
    # Password salah (401) dan akun nonaktif (403) sama-sama dihitung sebagai percobaan gagal.
    return respons.status_code in (401, 403)


def _email_mentah() -> str | None:
    data = request.get_json(silent=True)
    # flask-openapi3 juga menerima body berupa string JSON (dibuka satu tingkat), jadi dibaca dengan cara sama.
    if isinstance(data, str):
        try:
            data = current_app.json.loads(data)
        except ValueError:
            return None
    email = data.get("email") if isinstance(data, dict) else None
    return email if isinstance(email, str) else None


def _kunci_email() -> str:
    email = _email_mentah()
    # Email yang kosong atau terlalu panjang pasti ditolak validasi (422). Normalisasi tidak dijalankan
    # karena biaya validasi email panjang tumbuh kuadratik dan bisa dipakai untuk membebani server.
    if email is None or len(email) > PANJANG_MAKS_EMAIL:
        return "login-email:"
    try:
        return "login-email:" + normalisasi_email(email)
    except ValueError:
        return "login-email:" + email.strip().lower()


def _kunci_ip() -> str:
    return "login-ip:" + get_remote_address()


def _respons_sesi(pengguna: Pengguna, **token: str | int) -> dict:
    sesi = SesiResponse(pengguna=PenggunaResponse.model_validate(pengguna), **token)
    return sesi.model_dump(mode="json", exclude_none=True)


def _umur_access_token() -> int:
    return int(current_app.config["JWT_ACCESS_TOKEN_EXPIRES"].total_seconds())


def _umur_refresh_token() -> int:
    return int(current_app.config["JWT_REFRESH_TOKEN_EXPIRES"].total_seconds())


@auth_bp.post(
    "/login",
    summary="Masuk dengan email dan password",
    responses={200: SesiResponse, **respons_problem_doc(400, 401, 403, 429)},
)
# Batas 5 kali gagal per 15 menit, dihitung terpisah per email dan per alamat IP (Desain 2.1).
@limiter.limit(_batas_login, key_func=_kunci_email, deduct_when=_login_gagal)
@limiter.limit(_batas_login, key_func=_kunci_ip, deduct_when=_login_gagal)
# validate_request di posisi terdalam supaya batas percobaan diperiksa sebelum isi request divalidasi.
@validate_request()
def login(body: LoginRequest, header: LoginHeader):
    service = AuthService()
    pengguna = service.login(body.email, body.password)
    access_token = service.buat_access_token(pengguna)
    refresh_token = service.buat_refresh_token(pengguna)

    if header.x_client == "mobile":
        return jsonify(
            _respons_sesi(
                pengguna,
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="Bearer",  # noqa: S106
                expires_in=_umur_access_token(),
            )
        )

    respons = jsonify(_respons_sesi(pengguna))
    # Umur cookie disamakan dengan umur token (bawaan Flask-JWT-Extended satu tahun).
    set_access_cookies(respons, access_token, max_age=_umur_access_token())
    set_refresh_cookies(respons, refresh_token, max_age=_umur_refresh_token())
    return respons


@auth_bp.post(
    "/refresh",
    summary="Memperbarui access token dengan refresh token",
    security=SEMUA_KANAL_REFRESH,
    responses={200: SesiResponse, **respons_problem_doc(401)},
)
@jwt_required(refresh=True)
def refresh():
    pengguna: Pengguna = get_current_user()
    access_token = AuthService.buat_access_token(pengguna)
    if get_jwt_request_location() == "cookies":
        respons = jsonify(_respons_sesi(pengguna))
        set_access_cookies(respons, access_token, max_age=_umur_access_token())
        return respons
    return jsonify(
        _respons_sesi(
            pengguna,
            access_token=access_token,
            token_type="Bearer",  # noqa: S106
            expires_in=_umur_access_token(),
        )
    )


@auth_bp.post(
    "/logout",
    summary="Keluar",
    description="Memakai refresh token supaya tetap berhasil walau access token sudah kedaluwarsa.",
    security=SEMUA_KANAL_REFRESH,
    responses={204: None, **respons_problem_doc(401)},
)
@jwt_required(refresh=True)
def logout():
    respons = Response(status=204)
    if get_jwt_request_location() == "cookies":
        unset_jwt_cookies(respons)
    # Klien mobile cukup menghapus token di flutter_secure_storage; server tidak menyimpan sesi.
    return respons


@auth_bp.get(
    "/me",
    summary="Profil pengguna yang sedang masuk",
    security=SEMUA_KANAL_ACCESS,
    responses={200: PenggunaResponse, **respons_problem_doc(401)},
)
@jwt_required()
def me():
    pengguna: Pengguna = get_current_user()
    return jsonify(PenggunaResponse.model_validate(pengguna).model_dump(mode="json"))
