"""Fixture pytest bersama.

Tes berjalan terhadap PostgreSQL sungguhan. Database tes dibuat ulang sekali per sesi lewat
migrasi (sekaligus menguji migrasi), lalu setiap tes berjalan di dalam transaksi yang di-rollback.
Aplikasi terhubung sebagai role aplikasi (TEST_DATABASE_URL), migrasi sebagai role pemilik
(TEST_DATABASE_URL_MIGRASI), sama seperti di produksi.
"""

import os
import uuid
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa
from bantuan import PASSWORD_TES
from dotenv import load_dotenv
from flask import Flask
from flask.testing import FlaskClient
from flask_migrate import upgrade
from sqlalchemy.engine import make_url
from sqlalchemy.orm import scoped_session, sessionmaker

from app import create_app
from app.config import normalisasi_url_database
from app.extensions import db, limiter
from app.models import Kunjungan, Pasien, Pengguna
from app.models.enums import JenisKelamin, Peran

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

KONFIGURASI_TES: dict[str, Any] = {
    "APP_ENV": "testing",
    "SECRET_KEY": "rahasia-flask-untuk-pengujian-" + "s" * 32,
    "JWT_SECRET_KEY": "rahasia-jwt-untuk-pengujian-" + "j" * 32,
    # Ditetapkan eksplisit supaya hasil tes tidak bergantung pada JUMLAH_PROXY di .env pengembang.
    "JUMLAH_PROXY": 0,
}


def ambil_url_tes(nama_env: str) -> str:
    url = normalisasi_url_database(os.environ.get(nama_env))
    if not url:
        pytest.exit(f"{nama_env} belum diisi. Lihat backend/.env.example.", returncode=2)
    if not (make_url(url).database or "").endswith("_test"):
        pytest.exit(f"Nama database pada {nama_env} wajib berakhiran _test karena akan dihapus.", returncode=2)
    return url


def buat_ulang_database(url_pemilik: str) -> None:
    url = make_url(url_pemilik)
    admin = sa.create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as koneksi:
        koneksi.execute(sa.text(f'DROP DATABASE IF EXISTS "{url.database}" WITH (FORCE)'))
        koneksi.execute(sa.text(f'CREATE DATABASE "{url.database}"'))
    admin.dispose()


def hapus_database(url_pemilik: str) -> None:
    url = make_url(url_pemilik)
    admin = sa.create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as koneksi:
        koneksi.execute(sa.text(f'DROP DATABASE IF EXISTS "{url.database}" WITH (FORCE)'))
    admin.dispose()


@pytest.fixture(scope="session")
def url_db() -> dict[str, str]:
    return {"aplikasi": ambil_url_tes("TEST_DATABASE_URL"), "migrasi": ambil_url_tes("TEST_DATABASE_URL_MIGRASI")}


@pytest.fixture(scope="session")
def konfigurasi_app(url_db: dict[str, str]) -> dict[str, Any]:
    """Konfigurasi lengkap untuk membuat instance aplikasi tambahan di dalam tes."""
    return {
        **KONFIGURASI_TES,
        "SQLALCHEMY_DATABASE_URI": url_db["aplikasi"],
        "SQLALCHEMY_MIGRASI_URI": url_db["migrasi"],
    }


@pytest.fixture(scope="session")
def app(konfigurasi_app: dict[str, Any], url_db: dict[str, str]) -> Iterator[Flask]:
    buat_ulang_database(url_db["migrasi"])
    aplikasi = create_app(konfigurasi_app)
    with aplikasi.app_context():
        upgrade()
    yield aplikasi
    with aplikasi.app_context():
        db.engine.dispose()
    hapus_database(url_db["migrasi"])


@pytest.fixture(autouse=True)
def sesi_db(app: Flask) -> Iterator[scoped_session]:
    """Satu transaksi luar per tes; commit di kode aplikasi menjadi savepoint lalu ikut di-rollback."""
    with app.app_context():
        koneksi = db.engine.connect()
        transaksi = koneksi.begin()
        sesi_asli = db.session
        # Sengaja tidak memakai db._make_scoped_session: Session Flask-SQLAlchemy mengabaikan bind ke
        # koneksi ini sehingga commit benar-benar tersimpan.
        db.session = scoped_session(
            sessionmaker(bind=koneksi, join_transaction_mode="create_savepoint", expire_on_commit=False)
        )
        limiter.reset()
        try:
            yield db.session
        finally:
            db.session.remove()
            db.session = sesi_asli
            if transaksi.is_active:
                transaksi.rollback()
            koneksi.close()


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()


@pytest.fixture
def buat_pengguna(sesi_db: scoped_session) -> Callable[..., Pengguna]:
    def _buat(
        peran: Peran = Peran.PERAWAT,
        email: str | None = None,
        password: str = PASSWORD_TES,
        aktif: bool = True,
    ) -> Pengguna:
        pengguna = Pengguna(
            nama=f"Pengguna {peran.value}",
            email=email or f"{peran.value}-{uuid.uuid4().hex[:8]}@smarttriage.demo",
            peran=peran,
            is_active=aktif,
        )
        pengguna.atur_password(password)
        sesi_db.add(pengguna)
        sesi_db.commit()
        return pengguna

    return _buat


@pytest.fixture
def kunjungan(sesi_db: scoped_session, buat_pengguna: Callable[..., Pengguna]) -> Kunjungan:
    perawat = buat_pengguna(Peran.PERAWAT)
    pasien = Pasien(
        didaftarkan_oleh=perawat.id_pengguna,
        nama="Pasien Simulasi",
        perkiraan_usia=40,
        jenis_kelamin=JenisKelamin.PEREMPUAN,
    )
    sesi_db.add(pasien)
    sesi_db.flush()
    kunjungan = Kunjungan(id_pasien=pasien.id_pasien)
    sesi_db.add(kunjungan)
    sesi_db.commit()
    return kunjungan
