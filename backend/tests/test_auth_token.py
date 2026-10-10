"""Refresh, logout, profil, dan error token (SKPL TC-17, Desain 7.1)."""

import uuid
from datetime import timedelta

import pytest
from bantuan import bearer, login_mobile, login_web, nilai_cookie
from flask_jwt_extended import create_access_token, create_refresh_token, decode_token

from app.middleware.auth import _perlu_token_baru, _token_dicabut, _verifikasi_token_gagal
from app.models.enums import Peran
from app.utils.errors import Tipe


def _token_kedaluwarsa(app, pengguna, refresh=False) -> str:
    with app.app_context():
        pembuat = create_refresh_token if refresh else create_access_token
        return pembuat(identity=str(pengguna.id_pengguna), expires_delta=timedelta(seconds=-10))


def _cookie_dihapus(respons) -> set[str]:
    return {
        baris.split("=", 1)[0]
        for baris in respons.headers.getlist("Set-Cookie")
        if "Expires=Thu, 01 Jan 1970" in baris or "Max-Age=0" in baris
    }


# ---------------------------------------------------------------- /me


def test_me_dengan_cookie_dan_bearer(client, app, buat_pengguna):
    admin = buat_pengguna(Peran.ADMIN)
    login_web(client, admin.email)
    assert client.get("/api/v1/auth/me").get_json()["email"] == admin.email

    token = login_mobile(app.test_client(), admin.email).get_json()["access_token"]
    respons = app.test_client().get("/api/v1/auth/me", headers=bearer(token))
    assert respons.status_code == 200
    assert respons.get_json()["peran"] == "admin"


def test_me_tanpa_token_dibalas_401(client):
    respons = client.get("/api/v1/auth/me")
    assert respons.status_code == 401
    assert respons.content_type == "application/problem+json"
    assert respons.get_json()["type"] == Tipe.TIDAK_TERAUTENTIKASI


def test_token_rusak_dibalas_401_bukan_422(client):
    respons = client.get("/api/v1/auth/me", headers=bearer("bukan.token.jwt"))
    assert respons.status_code == 401
    assert respons.get_json()["type"] == Tipe.TOKEN_TIDAK_VALID


def test_refresh_token_tidak_bisa_dipakai_sebagai_access_token(client, buat_pengguna):
    refresh = login_mobile(client, buat_pengguna().email).get_json()["refresh_token"]
    respons = client.get("/api/v1/auth/me", headers=bearer(refresh))
    assert respons.status_code == 401
    isi = respons.get_json()
    assert isi["type"] == Tipe.TOKEN_TIDAK_VALID
    assert isi["detail"] == "Jenis token tidak sesuai untuk alamat ini."


def test_access_token_kedaluwarsa_ditandai_supaya_klien_refresh(client, app, buat_pengguna):
    # TC-17: klien membedakan token kedaluwarsa (cukup refresh) dari sesi berakhir (login ulang).
    perawat = buat_pengguna()
    respons = client.get("/api/v1/auth/me", headers=bearer(_token_kedaluwarsa(app, perawat)))
    assert respons.status_code == 401
    assert respons.get_json()["type"] == Tipe.TOKEN_KEDALUWARSA

    refresh = login_mobile(client, perawat.email).get_json()["refresh_token"]
    baru = client.post("/api/v1/auth/refresh", headers=bearer(refresh)).get_json()["access_token"]
    assert client.get("/api/v1/auth/me", headers=bearer(baru)).status_code == 200


def test_akun_dinonaktifkan_langsung_kehilangan_akses(client, buat_pengguna, sesi_db):
    perawat = buat_pengguna()
    token = login_mobile(client, perawat.email).get_json()
    perawat.is_active = False
    sesi_db.commit()

    for respons in (
        client.get("/api/v1/auth/me", headers=bearer(token["access_token"])),
        client.post("/api/v1/auth/refresh", headers=bearer(token["refresh_token"])),
    ):
        assert respons.status_code == 401
        assert respons.get_json()["type"] == Tipe.SESI_BERAKHIR


@pytest.mark.parametrize("identitas", [str(uuid.uuid4()), "bukan-uuid"])
def test_token_untuk_pengguna_yang_tidak_ada_ditolak(client, app, identitas):
    with app.app_context():
        token = create_access_token(identity=identitas)
    respons = client.get("/api/v1/auth/me", headers=bearer(token))
    assert respons.status_code == 401
    assert respons.get_json()["type"] == Tipe.SESI_BERAKHIR


# ---------------------------------------------------------------- /refresh


def test_refresh_lewat_cookie_wajib_csrf(client, buat_pengguna):
    login_web(client, buat_pengguna().email)

    tanpa_csrf = client.post("/api/v1/auth/refresh")
    assert tanpa_csrf.status_code == 401
    assert tanpa_csrf.get_json()["title"] == "Token CSRF tidak valid"

    # Token CSRF milik access token tidak berlaku untuk refresh.
    salah = client.post("/api/v1/auth/refresh", headers={"X-CSRF-TOKEN": nilai_cookie(client, "csrf_access_token")})
    assert salah.status_code == 401

    respons = client.post("/api/v1/auth/refresh", headers={"X-CSRF-TOKEN": nilai_cookie(client, "csrf_refresh_token")})
    assert respons.status_code == 200
    assert "access_token" not in respons.get_json()
    set_cookie = respons.headers.getlist("Set-Cookie")
    assert any(baris.startswith("access_token_cookie=") for baris in set_cookie)
    assert not any(baris.startswith("refresh_token_cookie=") for baris in set_cookie)


def test_refresh_lewat_bearer_mengembalikan_access_token_baru(client, buat_pengguna):
    refresh = login_mobile(client, buat_pengguna(Peran.DOKTER).email).get_json()["refresh_token"]
    respons = client.post("/api/v1/auth/refresh", headers=bearer(refresh))

    assert respons.status_code == 200
    assert respons.headers.getlist("Set-Cookie") == []
    isi = respons.get_json()
    assert isi["token_type"] == "Bearer"
    assert isi["expires_in"] == 900
    token_baru = decode_token(isi["access_token"])
    assert token_baru["exp"] - token_baru["iat"] == 15 * 60
    assert "refresh_token" not in isi
    assert isi["pengguna"]["peran"] == "dokter"


def test_access_token_tidak_bisa_dipakai_untuk_refresh(client, buat_pengguna):
    access = login_mobile(client, buat_pengguna().email).get_json()["access_token"]
    respons = client.post("/api/v1/auth/refresh", headers=bearer(access))
    assert respons.status_code == 401
    assert respons.get_json()["type"] == Tipe.TOKEN_TIDAK_VALID


def test_refresh_token_kedaluwarsa_berarti_sesi_berakhir(client, app, buat_pengguna):
    respons = client.post("/api/v1/auth/refresh", headers=bearer(_token_kedaluwarsa(app, buat_pengguna(), True)))
    assert respons.status_code == 401
    assert respons.get_json()["type"] == Tipe.SESI_BERAKHIR


def test_refresh_membaca_peran_terbaru_dari_basis_data(client, buat_pengguna, sesi_db):
    pengguna = buat_pengguna(Peran.PERAWAT)
    refresh = login_mobile(client, pengguna.email).get_json()["refresh_token"]
    pengguna.peran = Peran.DOKTER
    sesi_db.commit()

    access = client.post("/api/v1/auth/refresh", headers=bearer(refresh)).get_json()["access_token"]
    assert decode_token(access)["role"] == "dokter"


# ---------------------------------------------------------------- /logout


def test_logout_web_menghapus_semua_cookie(client, buat_pengguna):
    login_web(client, buat_pengguna().email)
    respons = client.post("/api/v1/auth/logout", headers={"X-CSRF-TOKEN": nilai_cookie(client, "csrf_refresh_token")})

    assert respons.status_code == 204
    assert _cookie_dihapus(respons) == {
        "access_token_cookie",
        "csrf_access_token",
        "refresh_token_cookie",
        "csrf_refresh_token",
    }
    assert client.get("/api/v1/auth/me").status_code == 401


def test_logout_web_tetap_berhasil_setelah_access_token_kedaluwarsa(client, app, buat_pengguna):
    perawat = buat_pengguna()
    login_web(client, perawat.email)
    client.set_cookie("access_token_cookie", _token_kedaluwarsa(app, perawat), path="/api/v1")

    respons = client.post("/api/v1/auth/logout", headers={"X-CSRF-TOKEN": nilai_cookie(client, "csrf_refresh_token")})
    assert respons.status_code == 204
    assert "refresh_token_cookie" in _cookie_dihapus(respons)


def test_logout_mobile_tanpa_cookie(client, buat_pengguna):
    refresh = login_mobile(client, buat_pengguna().email).get_json()["refresh_token"]
    respons = client.post("/api/v1/auth/logout", headers=bearer(refresh))
    assert respons.status_code == 204
    assert respons.headers.getlist("Set-Cookie") == []


def test_logout_tanpa_token_dibalas_401(client):
    assert client.post("/api/v1/auth/logout").status_code == 401


# ---------------------------------------------------------------- loader yang jarang terpicu


@pytest.mark.parametrize(
    ("loader", "tipe"),
    [
        (_token_dicabut, Tipe.SESI_BERAKHIR),
        (_perlu_token_baru, Tipe.TIDAK_TERAUTENTIKASI),
        (_verifikasi_token_gagal, Tipe.TOKEN_TIDAK_VALID),
    ],
)
def test_loader_jwt_lain_berformat_problem_details(app, loader, tipe):
    with app.test_request_context("/api/v1/auth/me"):
        respons = loader({}, {})
    assert respons.status_code == 401
    assert respons.mimetype == "application/problem+json"
    assert respons.get_json()["type"] == tipe
