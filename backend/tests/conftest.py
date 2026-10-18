"""Fixture pytest bersama.

Tes berjalan terhadap PostgreSQL sungguhan. Database tes dibuat ulang sekali per sesi lewat
migrasi (sekaligus menguji migrasi), lalu setiap tes berjalan di dalam transaksi yang di-rollback.
Aplikasi terhubung sebagai role aplikasi (TEST_DATABASE_URL), migrasi sebagai role pemilik
(TEST_DATABASE_URL_MIGRASI), sama seperti di produksi.
"""

import os
import uuid
from collections.abc import Callable, Iterator
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa
from bantuan import PASSWORD_TES, header_masuk
from dotenv import load_dotenv
from flask import Flask
from flask.testing import FlaskClient
from flask_migrate import upgrade
from sqlalchemy.engine import make_url
from sqlalchemy.orm import scoped_session, sessionmaker

from app import create_app
from app.config import normalisasi_url_database
from app.extensions import db, limiter
from app.models import Kunjungan, Pasien, Pengguna, Triase
from app.models.enums import (
    JenisKelamin,
    JenisTriase,
    Peran,
    RiskLevel,
    StatusKunjungan,
    StatusValidasi,
    SumberRekomendasi,
    SumberTandaVital,
    TingkatKesadaran,
)

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

KONFIGURASI_TES: dict[str, Any] = {
    "APP_ENV": "testing",
    "SECRET_KEY": "rahasia-flask-untuk-pengujian-" + "s" * 32,
    "JWT_SECRET_KEY": "rahasia-jwt-untuk-pengujian-" + "j" * 32,
    # Ditetapkan eksplisit supaya hasil tes tidak bergantung pada JUMLAH_PROXY di .env pengembang.
    "JUMLAH_PROXY": 0,
    # Model YOLO belum ada di repo; tes memakai pembaca tiruan, dan jalur ONNX diuji dengan model kecil buatan tes.
    "PEMBACA_LAYAR": "tiruan",
    # Groq tidak pernah dipanggil di tes; Eir memakai LLM tiruan dan klien Groq diuji dengan klien palsu.
    "LLM_EIR": "tiruan",
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
def sesi_db(request: pytest.FixtureRequest, app: Flask) -> Iterator[scoped_session]:
    """Satu transaksi luar per tes; commit di kode aplikasi menjadi savepoint lalu ikut di-rollback.

    Tes bertanda tanpa_rollback (misalnya tes konkurensi dua koneksi) memakai sesi biasa yang benar-benar
    commit; datanya dibersihkan fixture data_nyata.
    """
    if request.node.get_closest_marker("tanpa_rollback"):
        with app.app_context():
            limiter.reset()
            yield db.session
            db.session.remove()
        return
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


@pytest.fixture
def buat_kunjungan(sesi_db: scoped_session, buat_pengguna: Callable[..., Pengguna]) -> Callable[..., Kunjungan]:
    """Kunjungan baru untuk pasien baru, dengan waktu datang dan status yang bisa diatur."""
    perawat = buat_pengguna(Peran.PERAWAT)

    def _buat(
        nama: str = "Pasien Simulasi",
        waktu_datang: datetime | None = None,
        status: StatusKunjungan = StatusKunjungan.MENUNGGU,
        **pasien: Any,
    ) -> Kunjungan:
        data_pasien = {"perkiraan_usia": 40, "jenis_kelamin": JenisKelamin.PEREMPUAN, **pasien}
        baru = Pasien(didaftarkan_oleh=perawat.id_pengguna, nama=nama, **data_pasien)
        sesi_db.add(baru)
        sesi_db.flush()
        kunjungan = Kunjungan(id_pasien=baru.id_pasien, status=status)
        if waktu_datang is not None:
            kunjungan.waktu_datang = waktu_datang
        sesi_db.add(kunjungan)
        sesi_db.commit()
        return kunjungan

    return _buat


@pytest.fixture
def buat_triase(sesi_db: scoped_session, buat_pengguna: Callable[..., Pengguna]) -> Callable[..., Triase]:
    """Triase langsung di basis data dengan level dan status pilihan, tanpa melewati model."""
    perawat = buat_pengguna(Peran.PERAWAT)

    def _buat(
        kunjungan: Kunjungan,
        risk_level: RiskLevel = RiskLevel.SEDANG,
        status: StatusValidasi = StatusValidasi.MENUNGGU,
        waktu: datetime | None = None,
        jenis: JenisTriase | None = None,
    ) -> Triase:
        if jenis is None:
            sudah_ada = sesi_db.query(Triase).filter_by(id_kunjungan=kunjungan.id_kunjungan).count()
            jenis = JenisTriase.ULANG if sudah_ada else JenisTriase.AWAL
        triase = Triase(
            id_kunjungan=kunjungan.id_kunjungan,
            jenis=jenis,
            dibuat_oleh=perawat.id_pengguna,
            keluhan_utama="Pusing",
            gejala="Pusing berputar sejak pagi tanpa muntah",
            skala_nyeri=3,
            tingkat_kesadaran=TingkatKesadaran.SADAR_PENUH,
            td_sistolik=120,
            td_diastolik=80,
            nadi=80,
            laju_napas=18,
            suhu=Decimal("36.8"),
            saturasi=Decimal("98.0"),
            sumber_tanda_vital=SumberTandaVital.MANUAL,
            risk_level=risk_level,
            sumber_rekomendasi=SumberRekomendasi.MODEL,
            penjelasan_ai={"versi_model": None, "faktor": [], "probabilitas": None},
            status_validasi=status,
        )
        if waktu is not None:
            triase.waktu_triase = waktu
        sesi_db.add(triase)
        sesi_db.commit()
        return triase

    return _buat


@pytest.fixture
def masuk(client: FlaskClient, buat_pengguna: Callable[..., Pengguna]) -> Callable[[Peran], tuple[Pengguna, dict]]:
    """Membuat pengguna dengan peran tertentu lalu mengembalikan pengguna dan header Authorization-nya."""

    def _masuk(peran: Peran) -> tuple[Pengguna, dict[str, str]]:
        pengguna = buat_pengguna(peran)
        return pengguna, header_masuk(client, pengguna.email)

    return _masuk


@pytest.fixture(scope="session")
def app_tanpa_model(konfigurasi_app: dict[str, Any], app: Flask) -> Flask:
    """Aplikasi yang model triasenya tidak bisa dimuat, untuk menguji aturan cadangan (SKPL TC-09)."""
    return create_app({**konfigurasi_app, "MODEL_RF_PATH": "/tidak/ada/model_rf.joblib"})


@pytest.fixture
def data_nyata(url_db: dict[str, str]) -> Iterator[None]:
    """Mengosongkan tabel lewat role pemilik setelah tes tanpa_rollback (role aplikasi tidak boleh menghapus log)."""
    yield
    # Request di thread utama memakai app context fixture, jadi sesinya baru ditutup di sini. Tanpa ini,
    # transaksi yang masih terbuka menahan TRUNCATE.
    db.session.remove()
    mesin = sa.create_engine(url_db["migrasi"])
    with mesin.begin() as koneksi:
        koneksi.execute(sa.text("SET LOCAL lock_timeout = '10s'"))
        koneksi.execute(sa.text("TRUNCATE log_audit, pemindaian_alat, sesi_eir, triase, kunjungan, pasien, pengguna"))
    mesin.dispose()
