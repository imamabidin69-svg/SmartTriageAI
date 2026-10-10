"""Migrasi awal: naik-turun-naik, kesesuaian dengan model, nilai ENUM, dan hak akses role aplikasi."""

from decimal import Decimal

import pytest
import sqlalchemy as sa
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from conftest import buat_ulang_database, hapus_database
from flask_migrate import downgrade, upgrade
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ProgrammingError

from app import create_app
from app.extensions import db
from app.models import KONFIGURASI_BAWAAN, Konfigurasi, LogAudit
from app.models.enums import SEMUA_TIPE_ENUM, AksiAudit, KategoriKeluhan, Peran

TABEL_PDM = {"pengguna", "pasien", "kunjungan", "triase", "pemindaian_alat", "sesi_eir", "log_audit", "konfigurasi"}


@pytest.fixture
def url_db_sementara(url_db):
    url = make_url(url_db["migrasi"])
    url = url.set(database=url.database.removesuffix("_test") + "_migrasi_test").render_as_string(hide_password=False)
    buat_ulang_database(url)
    yield url
    hapus_database(url)


def _isi_skema(url: str) -> tuple[set[str], set[str]]:
    mesin = sa.create_engine(url)
    with mesin.connect() as koneksi:
        tabel = set(koneksi.scalars(sa.text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")))
        tipe = set(koneksi.scalars(sa.text("SELECT typname FROM pg_type WHERE typtype = 'e'")))
    mesin.dispose()
    return tabel, tipe


def test_migrasi_naik_turun_naik(konfigurasi_app, url_db_sementara):
    aplikasi = create_app(
        {**konfigurasi_app, "SQLALCHEMY_DATABASE_URI": url_db_sementara, "SQLALCHEMY_MIGRASI_URI": url_db_sementara}
    )
    nama_enum = {tipe.name for tipe in SEMUA_TIPE_ENUM}
    with aplikasi.app_context():
        upgrade()
        tabel, tipe = _isi_skema(url_db_sementara)
        assert tabel == TABEL_PDM | {"alembic_version"}
        assert tipe == nama_enum

        downgrade(revision="base")
        tabel, tipe = _isi_skema(url_db_sementara)
        assert tabel == {"alembic_version"}
        assert tipe == set()

        upgrade()
        assert _isi_skema(url_db_sementara)[0] == TABEL_PDM | {"alembic_version"}
        db.engine.dispose()


def test_skema_basis_data_sama_dengan_model(app):
    with app.app_context(), db.engine.connect() as koneksi:
        konteks = MigrationContext.configure(koneksi, opts={"compare_type": True})
        assert compare_metadata(konteks, db.metadata) == []


@pytest.mark.parametrize("tipe", SEMUA_TIPE_ENUM, ids=lambda t: t.name)
def test_label_enum_di_basis_data_sama_dengan_python(sesi_db, tipe):
    label = sesi_db.scalars(
        sa.text(
            "SELECT e.enumlabel FROM pg_enum e JOIN pg_type t ON t.oid = e.enumtypid "
            "WHERE t.typname = :nama ORDER BY e.enumsortorder"
        ),
        {"nama": tipe.name},
    ).all()
    assert label == [anggota.value for anggota in tipe.enum_class]


def test_kategori_keluhan_sama_dengan_kategori_latih_model():
    assert len(KategoriKeluhan) == 18
    assert KategoriKeluhan.MUAL_MUNTAH_ATAU_DIARE == "Mual, muntah, atau diare"
    assert KategoriKeluhan.LAINNYA == "Lainnya"


def test_baris_konfigurasi_bawaan(sesi_db):
    konfigurasi = sesi_db.get(Konfigurasi, 1)
    assert konfigurasi is not None
    for kolom, nilai in KONFIGURASI_BAWAAN.items():
        assert getattr(konfigurasi, kolom) == nilai
    assert konfigurasi.ambang_keyakinan == Decimal("0.85")


def _sqlstate(galat: pytest.ExceptionInfo) -> str:
    return galat.value.orig.sqlstate


def test_role_aplikasi_tidak_bisa_mengubah_atau_menghapus_log_audit(sesi_db, buat_pengguna):
    dokter = buat_pengguna(Peran.DOKTER)
    sesi_db.add(LogAudit(id_aktor=dokter.id_pengguna, aksi=AksiAudit.UBAH_KONFIGURASI, catatan="ambang diubah"))
    sesi_db.commit()
    assert sesi_db.scalar(sa.text("SELECT current_user")) == "smarttriage_app"

    for perintah in (
        "UPDATE log_audit SET catatan = 'diubah'",
        "DELETE FROM log_audit",
        "TRUNCATE log_audit",
    ):
        with pytest.raises(ProgrammingError) as galat, sesi_db.begin_nested():
            sesi_db.execute(sa.text(perintah))
        assert _sqlstate(galat) == "42501", perintah

    assert sesi_db.scalar(sa.select(sa.func.count()).select_from(LogAudit)) == 1


def test_role_aplikasi_tidak_bisa_mengubah_skema(sesi_db):
    for perintah in ("CREATE TABLE coba (id int)", "DROP TABLE pengguna", "SELECT * FROM alembic_version"):
        with pytest.raises(ProgrammingError) as galat, sesi_db.begin_nested():
            sesi_db.execute(sa.text(perintah))
        assert _sqlstate(galat) == "42501", perintah
