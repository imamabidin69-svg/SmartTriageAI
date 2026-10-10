import sqlalchemy as sa
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import scoped_session, sessionmaker

from app.extensions import db
from app.services.health_service import (
    HealthService,
    PemeriksaDatabase,
    PemeriksaHakAksesLogAudit,
    PemeriksaKomponen,
)


class PemeriksaTiruan(PemeriksaKomponen):
    def __init__(self, nama: str, wajib: bool, hasil: bool | Exception) -> None:
        self.nama = nama
        self.wajib = wajib
        self.hasil = hasil

    def cek(self) -> bool:
        if isinstance(self.hasil, Exception):
            raise self.hasil
        return self.hasil


def test_health_ok_tanpa_login(client):
    respons = client.get("/api/v1/health")
    assert respons.status_code == 200
    assert respons.get_json() == {"status": "ok", "komponen": {"database": "ok", "hak_akses_log_audit": "ok"}}


def test_health_503_bila_komponen_wajib_gagal(app, client, monkeypatch):
    monkeypatch.setitem(app.extensions, "pemeriksa_kesehatan", [PemeriksaTiruan("database", True, False)])
    respons = client.get("/api/v1/health")
    assert respons.status_code == 503
    assert respons.get_json() == {"status": "gagal", "komponen": {"database": "gagal"}}


def test_status_degraded_bila_komponen_tidak_wajib_gagal():
    hasil = HealthService([PemeriksaTiruan("database", True, True), PemeriksaTiruan("groq", False, False)]).periksa()
    assert hasil.status == "degraded"
    assert hasil.komponen == {"database": "ok", "groq": "gagal"}


def test_status_gagal_tetap_gagal_walau_ada_komponen_degraded():
    hasil = HealthService(
        [
            PemeriksaTiruan("model", False, False),
            PemeriksaTiruan("database", True, False),
            PemeriksaTiruan("onnx", False, False),
        ]
    ).periksa()
    assert hasil.status == "gagal"


def test_pemeriksa_yang_error_dianggap_gagal_tanpa_membocorkan_pesan(caplog):
    hasil = HealthService([PemeriksaTiruan("groq", False, RuntimeError("kunci-rahasia"))]).periksa()
    assert hasil.status == "degraded"
    assert "kunci-rahasia" not in hasil.model_dump_json()
    assert "pemeriksa groq error" in caplog.text


def test_pemeriksa_database_gagal_saat_koneksi_putus(app, monkeypatch):
    def gagal(*_args, **_kwargs):
        raise OperationalError("SELECT 1", {}, Exception('connection to server at "10.0.0.1" failed'))

    with app.app_context():
        monkeypatch.setattr(db.session, "execute", gagal)
        assert PemeriksaDatabase().cek() is False


def test_pemeriksa_database_sehat(app):
    with app.app_context():
        assert PemeriksaDatabase().cek() is True


def test_hak_akses_log_audit_sehat_untuk_role_aplikasi(app):
    with app.app_context():
        assert PemeriksaHakAksesLogAudit().cek() is True


def test_hak_akses_log_audit_gagal_bila_aplikasi_memakai_role_pemilik(app, url_db, monkeypatch, caplog):
    # Bila DATABASE_URL terisi role pemilik, log_audit bisa diubah; health check harus menolaknya (NFR-06).
    mesin = sa.create_engine(url_db["migrasi"])
    with mesin.connect() as koneksi, app.app_context():
        sesi_pemilik = scoped_session(sessionmaker(bind=koneksi))
        monkeypatch.setattr(db, "session", sesi_pemilik)
        assert PemeriksaHakAksesLogAudit().cek() is False
        sesi_pemilik.remove()
    mesin.dispose()
    assert "masih bisa mengubah log_audit" in caplog.text


def test_hak_akses_log_audit_gagal_saat_basis_data_error(app, monkeypatch):
    def gagal(*_args, **_kwargs):
        raise OperationalError("SELECT 1", {}, Exception("putus"))

    with app.app_context():
        monkeypatch.setattr(db.session, "scalar", gagal)
        assert PemeriksaHakAksesLogAudit().cek() is False
