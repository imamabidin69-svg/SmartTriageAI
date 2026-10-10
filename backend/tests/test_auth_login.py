"""Login web (cookie) dan mobile (token di body), SKPL TC-01 sampai TC-03."""

from bantuan import PASSWORD_TES, login_mobile, login_web
from flask_jwt_extended import decode_token

from app.models.enums import Peran
from app.services import auth_service
from app.utils.errors import Tipe

COOKIE_JWT = {"access_token_cookie", "csrf_access_token", "refresh_token_cookie", "csrf_refresh_token"}


def _set_cookie(respons) -> dict[str, str]:
    return {baris.split("=", 1)[0]: baris for baris in respons.headers.getlist("Set-Cookie")}


def test_login_web_menyimpan_token_di_cookie_httponly(client, buat_pengguna):
    perawat = buat_pengguna(Peran.PERAWAT)
    respons = login_web(client, perawat.email)

    assert respons.status_code == 200
    isi = respons.get_json()
    assert isi == {
        "pengguna": {
            "id_pengguna": str(perawat.id_pengguna),
            "nama": perawat.nama,
            "email": perawat.email,
            "peran": "perawat",
            "is_active": True,
        }
    }
    cookie = _set_cookie(respons)
    assert set(cookie) == COOKIE_JWT
    for nama in ("access_token_cookie", "refresh_token_cookie"):
        assert "HttpOnly" in cookie[nama]
        assert "Secure" in cookie[nama]
        assert "SameSite=Lax" in cookie[nama]
    # Token CSRF harus bisa dibaca JavaScript web admin untuk dikirim lewat header X-CSRF-TOKEN.
    assert "HttpOnly" not in cookie["csrf_access_token"]
    assert "HttpOnly" not in cookie["csrf_refresh_token"]
    assert "Path=/api/v1;" in cookie["access_token_cookie"] + ";"
    assert "Path=/api/v1/auth" in cookie["refresh_token_cookie"]
    # Umur cookie mengikuti umur token (15 menit dan 8 jam).
    assert "Max-Age=900" in cookie["access_token_cookie"]
    assert "Max-Age=28800" in cookie["refresh_token_cookie"]


def test_login_mobile_mengirim_token_di_body_tanpa_cookie(client, buat_pengguna):
    dokter = buat_pengguna(Peran.DOKTER)
    respons = login_mobile(client, dokter.email)

    assert respons.status_code == 200
    assert respons.headers.getlist("Set-Cookie") == []
    isi = respons.get_json()
    assert isi["token_type"] == "Bearer"
    assert isi["expires_in"] == 900
    assert isi["pengguna"]["peran"] == "dokter"

    access = decode_token(isi["access_token"])
    refresh = decode_token(isi["refresh_token"])
    assert access["type"] == "access"
    assert access["sub"] == str(dokter.id_pengguna)
    assert access["role"] == "dokter"
    assert access["exp"] - access["iat"] == 15 * 60
    assert refresh["type"] == "refresh"
    # Peran tidak disimpan di refresh token; diambil ulang dari basis data saat refresh.
    assert "role" not in refresh
    assert refresh["exp"] - refresh["iat"] == 8 * 3600


def test_header_x_client_tidak_peka_huruf_besar(client, buat_pengguna):
    perawat = buat_pengguna(Peran.PERAWAT)
    respons = client.post(
        "/api/v1/auth/login", json={"email": perawat.email, "password": PASSWORD_TES}, headers={"x-client": "mobile"}
    )
    assert "access_token" in respons.get_json()


def test_email_dinormalisasi_saat_login(client, buat_pengguna):
    buat_pengguna(Peran.ADMIN, email="admin.igd@smarttriage.demo")
    respons = login_web(client, "  Admin.IGD@SmartTriage.DEMO ")
    assert respons.status_code == 200
    assert respons.get_json()["pengguna"]["email"] == "admin.igd@smarttriage.demo"


def test_password_salah_dibalas_401_pesan_umum(client, buat_pengguna):
    perawat = buat_pengguna(Peran.PERAWAT)
    respons = login_web(client, perawat.email, "PasswordSalah")

    assert respons.status_code == 401
    assert respons.content_type == "application/problem+json"
    isi = respons.get_json()
    assert isi["type"] == Tipe.KREDENSIAL_SALAH
    assert isi["title"] == "Email atau password salah"
    assert respons.headers.getlist("Set-Cookie") == []


def test_email_tidak_terdaftar_dibalas_sama_dan_tetap_menghitung_hash(client, buat_pengguna, monkeypatch):
    perawat = buat_pengguna(Peran.PERAWAT)
    dipanggil = []
    asli = auth_service.check_password_hash

    def mata_mata(hash_password, password):
        dipanggil.append(hash_password)
        return asli(hash_password, password)

    monkeypatch.setattr(auth_service, "check_password_hash", mata_mata)
    tidak_ada = login_web(client, "tidak.ada@smarttriage.demo", "PasswordSalah").get_json()
    salah = login_web(client, perawat.email, "PasswordSalah").get_json()

    # Hash pembanding tetap dihitung supaya waktu respons tidak membocorkan keberadaan akun.
    assert len(dipanggil) == 1
    assert dipanggil[0].startswith("scrypt:")
    assert tidak_ada == salah


def test_akun_nonaktif_dengan_password_benar_dibalas_403(client, buat_pengguna):
    perawat = buat_pengguna(Peran.PERAWAT, aktif=False)
    respons = login_web(client, perawat.email)

    assert respons.status_code == 403
    isi = respons.get_json()
    assert isi["type"] == Tipe.AKUN_NONAKTIF
    assert isi["title"] == "Akun tidak aktif"
    assert respons.headers.getlist("Set-Cookie") == []


def test_akun_nonaktif_dengan_password_salah_tetap_401_umum(client, buat_pengguna):
    perawat = buat_pengguna(Peran.PERAWAT, aktif=False)
    respons = login_web(client, perawat.email, "PasswordSalah")
    assert respons.status_code == 401
    assert respons.get_json()["type"] == Tipe.KREDENSIAL_SALAH


def test_isian_kosong_dibalas_422_per_field(client):
    respons = client.post("/api/v1/auth/login", json={})
    assert respons.status_code == 422
    assert respons.content_type == "application/problem+json"
    isi = respons.get_json()
    assert isi["type"] == Tipe.VALIDASI
    assert isi["errors"] == [
        {"field": "email", "pesan": "Email wajib diisi."},
        {"field": "password", "pesan": "Password wajib diisi."},
    ]


def test_validasi_tidak_mengembalikan_isi_password(client):
    respons = client.post(
        "/api/v1/auth/login", json={"email": "bukan-email", "password": "RahasiaBocor99", "role": "admin"}
    )
    assert respons.status_code == 422
    assert "RahasiaBocor99" not in respons.get_data(as_text=True)
    assert respons.get_json()["errors"] == [
        {"field": "email", "pesan": "Format email tidak valid."},
        {"field": "role", "pesan": "Field role tidak dikenal."},
    ]


def test_password_terlalu_panjang_ditolak(client):
    respons = client.post("/api/v1/auth/login", json={"email": "a@smarttriage.demo", "password": "x" * 129})
    assert respons.get_json()["errors"] == [{"field": "password", "pesan": "Password maksimal 128 karakter."}]


def test_header_x_client_tidak_dikenal_ditolak(client):
    respons = client.post(
        "/api/v1/auth/login",
        json={"email": "a@smarttriage.demo", "password": "x"},
        headers={"X-Client": "tablet"},
    )
    assert respons.status_code == 422
    assert respons.get_json()["errors"] == [
        {"field": "X-Client", "pesan": "Header X-Client harus salah satu dari: 'web', 'mobile'."}
    ]


def test_isi_bukan_json_dibalas_400(client):
    for data, tipe_konten in (
        ("email=a", "application/x-www-form-urlencoded"),
        ("{rusak", "application/json"),
        # String JSON yang isinya bukan JSON (flask-openapi3 membuka string satu tingkat).
        ('"bukan json"', "application/json"),
        ('"[1, 2]"', "application/json"),
    ):
        respons = client.post("/api/v1/auth/login", data=data, content_type=tipe_konten)
        assert respons.status_code == 400
        assert respons.get_json()["type"] == Tipe.JSON_TIDAK_VALID
