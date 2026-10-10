"""Konfigurasi aplikasi per lingkungan (development, testing, production).

Nilai rahasia dan alamat basis data selalu dibaca dari environment variable,
tidak pernah ditulis di kode. Lihat .env.example untuk daftar variabelnya.
"""

import copy
import os
from collections.abc import Mapping
from datetime import timedelta
from typing import Any, ClassVar

LINGKUNGAN_VALID = ("development", "testing", "production")
PANJANG_MINIMAL_RAHASIA = 32
# Nilai contoh di .env.example. Aplikasi menolak start bila nilai ini masih dipakai.
PENANDA_CONTOH_RAHASIA = "ganti-dengan"


class KonfigurasiTidakValidError(RuntimeError):
    """Konfigurasi wajib kosong atau tidak aman sehingga aplikasi tidak boleh dijalankan."""


class Config:
    """Konfigurasi dasar yang berlaku di semua lingkungan."""

    APP_ENV = "production"
    TESTING = False

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Batas waktu koneksi supaya health check tidak menggantung saat basis data tidak terjangkau.
    SQLALCHEMY_ENGINE_OPTIONS: ClassVar[dict[str, Any]] = {
        "pool_pre_ping": True,
        "connect_args": {"connect_timeout": 3},
    }

    # Sesi JWT sesuai Desain Arsitektur Backend 7.1.
    JWT_TOKEN_LOCATION: ClassVar[list[str]] = ["cookies", "headers"]
    JWT_ALGORITHM = "HS256"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(hours=8)
    JWT_COOKIE_SECURE = True
    JWT_COOKIE_SAMESITE = "Lax"
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_ACCESS_COOKIE_PATH = "/api/v1"
    JWT_REFRESH_COOKIE_PATH = "/api/v1/auth"
    # False supaya cookie refresh tidak hilang saat peramban atau PWA ditutup di tengah shift.
    # Umur cookie diisi sama dengan umur token di routes/auth.py.
    JWT_SESSION_COOKIE = False

    # Pembatas percobaan login (Flask-Limiter, disimpan di memori proses).
    RATELIMIT_STORAGE_URI = "memory://"
    # Moving window: yang dihitung benar-benar kegagalan dalam 15 menit terakhir (SKPL Gambar 4.2),
    # bukan jendela tetap yang direset serentak setiap 15 menit.
    RATELIMIT_STRATEGY = "moving-window"
    RATELIMIT_HEADERS_ENABLED = True
    BATAS_LOGIN = "5 per 15 minutes"

    # Ukuran maksimal isi request (1 MiB). Endpoint unggah foto menaikkannya sendiri.
    MAX_CONTENT_LENGTH = 1024 * 1024

    # Jumlah proxy tepercaya di depan aplikasi. 0 berarti X-Forwarded-For diabaikan.
    JUMLAH_PROXY = 0
    HSTS_AKTIF = False
    # Spesifikasi OpenAPI dan Swagger UI hanya disajikan di development. Untuk klien Dart,
    # spesifikasi diekspor dengan perintah `flask openapi -o openapi.json`.
    DOKUMENTASI_API_AKTIF = False
    PREFIKS_DOKUMENTASI = "/api/v1/openapi"


class DevelopmentConfig(Config):
    APP_ENV = "development"
    # Uji lewat IP LAN tanpa HTTPS akan membuang cookie Secure, jadi dimatikan khusus development.
    JWT_COOKIE_SECURE = False
    DOKUMENTASI_API_AKTIF = True


class TestingConfig(Config):
    APP_ENV = "testing"
    TESTING = True


class ProductionConfig(Config):
    APP_ENV = "production"
    HSTS_AKTIF = True


KELAS_KONFIGURASI: dict[str, type[Config]] = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def normalisasi_url_database(url: str | None) -> str | None:
    """Mengubah skema URL PostgreSQL ke driver psycopg 3.

    URL dari Supabase atau Railway biasanya berawalan postgres:// atau postgresql://,
    sedangkan SQLAlchemy tanpa psycopg2 hanya mengenali postgresql+psycopg://.
    """
    if not url:
        return url
    for awalan in ("postgres://", "postgresql://"):
        if url.startswith(awalan):
            return "postgresql+psycopg://" + url[len(awalan) :]
    return url


def _ambil_env(nama: str) -> str | None:
    nilai = os.environ.get(nama)
    return nilai.strip() if nilai and nilai.strip() else None


def buat_konfigurasi(nama_env: str) -> dict[str, Any]:
    """Menyusun konfigurasi dari kelas lingkungan dan environment variable saat ini."""
    if nama_env not in KELAS_KONFIGURASI:
        raise KonfigurasiTidakValidError(
            f"APP_ENV '{nama_env}' tidak dikenal. Pilih salah satu: {', '.join(LINGKUNGAN_VALID)}."
        )
    kelas = KELAS_KONFIGURASI[nama_env]
    # Disalin dalam supaya nilai bertipe list/dict tidak terbagi antar-instance aplikasi.
    konfigurasi = {kunci: copy.deepcopy(getattr(kelas, kunci)) for kunci in dir(kelas) if kunci.isupper()}

    url_aplikasi = normalisasi_url_database(_ambil_env("DATABASE_URL"))
    konfigurasi["SQLALCHEMY_DATABASE_URI"] = url_aplikasi
    # Migrasi dijalankan role pemilik skema; aplikasi memakai role yang hak aksesnya dibatasi.
    konfigurasi["SQLALCHEMY_MIGRASI_URI"] = normalisasi_url_database(_ambil_env("DATABASE_URL_MIGRASI")) or url_aplikasi
    konfigurasi["SECRET_KEY"] = _ambil_env("SECRET_KEY")
    konfigurasi["JWT_SECRET_KEY"] = _ambil_env("JWT_SECRET_KEY")

    jumlah_proxy = _ambil_env("JUMLAH_PROXY")
    if jumlah_proxy is not None:
        konfigurasi["JUMLAH_PROXY"] = jumlah_proxy
    return konfigurasi


def validasi_konfigurasi(konfigurasi: Mapping[str, Any]) -> None:
    """Menghentikan start aplikasi bila konfigurasi wajib kosong atau rahasia tidak aman."""
    masalah: list[str] = []

    if not konfigurasi.get("SQLALCHEMY_DATABASE_URI"):
        masalah.append("DATABASE_URL wajib diisi.")

    for nama in ("SECRET_KEY", "JWT_SECRET_KEY"):
        nilai = konfigurasi.get(nama)
        if not nilai:
            masalah.append(f"{nama} wajib diisi.")
        elif PENANDA_CONTOH_RAHASIA in nilai:
            masalah.append(f"{nama} masih memakai nilai contoh dari .env.example.")
        elif len(nilai.encode()) < PANJANG_MINIMAL_RAHASIA:
            masalah.append(f"{nama} minimal {PANJANG_MINIMAL_RAHASIA} byte.")

    secret_key = konfigurasi.get("SECRET_KEY")
    if secret_key and secret_key == konfigurasi.get("JWT_SECRET_KEY"):
        masalah.append("SECRET_KEY dan JWT_SECRET_KEY harus berbeda.")

    try:
        jumlah_proxy = int(konfigurasi.get("JUMLAH_PROXY", 0))
        if jumlah_proxy < 0:
            raise ValueError
    except (TypeError, ValueError):
        masalah.append("JUMLAH_PROXY harus bilangan bulat 0 atau lebih.")

    if masalah:
        raise KonfigurasiTidakValidError("Konfigurasi tidak valid: " + " ".join(masalah))
