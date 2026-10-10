import pytest
from werkzeug.middleware.proxy_fix import ProxyFix

from app import create_app
from app.config import KonfigurasiTidakValidError, buat_konfigurasi, normalisasi_url_database, validasi_konfigurasi

RAHASIA_A = "a" * 40
RAHASIA_B = "b" * 40


def konfigurasi_valid(**ubah):
    nilai = {
        "SQLALCHEMY_DATABASE_URI": "postgresql+psycopg://u:p@localhost/db",
        "SECRET_KEY": RAHASIA_A,
        "JWT_SECRET_KEY": RAHASIA_B,
        "JUMLAH_PROXY": 0,
    }
    nilai.update(ubah)
    return nilai


@pytest.mark.parametrize(
    ("masukan", "hasil"),
    [
        ("postgres://u:p@h:5432/db", "postgresql+psycopg://u:p@h:5432/db"),
        ("postgresql://u:p@h/db?sslmode=require", "postgresql+psycopg://u:p@h/db?sslmode=require"),
        ("postgresql+psycopg://u:p@h/db", "postgresql+psycopg://u:p@h/db"),
        (None, None),
        ("", ""),
    ],
)
def test_normalisasi_url_database(masukan, hasil):
    assert normalisasi_url_database(masukan) == hasil


def test_buat_konfigurasi_membaca_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://app:p@h/db")
    monkeypatch.delenv("DATABASE_URL_MIGRASI", raising=False)
    monkeypatch.setenv("SECRET_KEY", f"  {RAHASIA_A}  ")
    monkeypatch.setenv("JUMLAH_PROXY", "1")
    nilai = buat_konfigurasi("production")
    assert nilai["SQLALCHEMY_DATABASE_URI"] == "postgresql+psycopg://app:p@h/db"
    # Tanpa DATABASE_URL_MIGRASI, migrasi memakai URL yang sama.
    assert nilai["SQLALCHEMY_MIGRASI_URI"] == nilai["SQLALCHEMY_DATABASE_URI"]
    assert nilai["SECRET_KEY"] == RAHASIA_A
    assert nilai["JUMLAH_PROXY"] == "1"
    assert nilai["JWT_COOKIE_SECURE"] is True
    assert nilai["HSTS_AKTIF"] is True


def test_buat_konfigurasi_development_mematikan_cookie_secure():
    nilai = buat_konfigurasi("development")
    assert nilai["JWT_COOKIE_SECURE"] is False
    assert nilai["DOKUMENTASI_API_AKTIF"] is True


def test_nilai_list_tidak_terbagi_antar_konfigurasi():
    pertama = buat_konfigurasi("testing")
    kedua = buat_konfigurasi("testing")
    pertama["JWT_TOKEN_LOCATION"].append("query_string")
    assert kedua["JWT_TOKEN_LOCATION"] == ["cookies", "headers"]


def test_app_env_tidak_dikenal_ditolak():
    with pytest.raises(KonfigurasiTidakValidError, match="APP_ENV 'staging' tidak dikenal"):
        buat_konfigurasi("staging")


def test_konfigurasi_valid_lolos():
    validasi_konfigurasi(konfigurasi_valid())


@pytest.mark.parametrize(
    ("ubah", "pesan"),
    [
        ({"SQLALCHEMY_DATABASE_URI": None}, "DATABASE_URL wajib diisi"),
        ({"SECRET_KEY": None}, "SECRET_KEY wajib diisi"),
        ({"JWT_SECRET_KEY": "ganti-dengan-rahasia-acak-lain-minimal-32-byte"}, "JWT_SECRET_KEY masih memakai nilai"),
        ({"JWT_SECRET_KEY": "pendek"}, "JWT_SECRET_KEY minimal 32 byte"),
        ({"JWT_SECRET_KEY": RAHASIA_A}, "harus berbeda"),
        ({"JUMLAH_PROXY": "satu"}, "JUMLAH_PROXY harus bilangan bulat"),
        ({"JUMLAH_PROXY": -1}, "JUMLAH_PROXY harus bilangan bulat"),
    ],
)
def test_konfigurasi_tidak_aman_ditolak(ubah, pesan):
    with pytest.raises(KonfigurasiTidakValidError, match=pesan):
        validasi_konfigurasi(konfigurasi_valid(**ubah))


def test_create_app_menolak_start_tanpa_rahasia(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    with pytest.raises(KonfigurasiTidakValidError):
        create_app({"APP_ENV": "production", "SQLALCHEMY_DATABASE_URI": "postgresql+psycopg://u:p@h/db"})


def test_create_app_bawaannya_production(monkeypatch, konfigurasi_app):
    monkeypatch.delenv("APP_ENV", raising=False)
    konfigurasi = {k: v for k, v in konfigurasi_app.items() if k != "APP_ENV"}
    aplikasi = create_app(konfigurasi)
    assert aplikasi.config["APP_ENV"] == "production"
    assert aplikasi.config["JWT_COOKIE_SECURE"] is True
    assert not isinstance(aplikasi.wsgi_app, ProxyFix)


def test_proxyfix_aktif_bila_ada_proxy_tepercaya(konfigurasi_app):
    aplikasi = create_app({**konfigurasi_app, "JUMLAH_PROXY": 1})
    assert isinstance(aplikasi.wsgi_app, ProxyFix)
