import json
import logging

import pytest
from sqlalchemy import select

from app.cli import AKUN_DEMO, PASIEN_SIMULASI
from app.models import Kunjungan, Pasien, Pengguna, Triase
from app.models.enums import JenisTriase, StatusValidasi
from app.services.daftar_tunggu_service import URUTAN_LEVEL
from app.services.peringatan_service import PeringatanService
from app.utils.log import PemformatJson, _HandlerSmartTriage, atur_logging
from app.utils.schemas import LoginRequest, normalisasi_email


@pytest.fixture
def password_demo(monkeypatch):
    nilai = {env: f"Demo-{env[-6:]}-123" for *_, env in AKUN_DEMO}
    for env, password in nilai.items():
        monkeypatch.setenv(env, password)
    return nilai


def test_seed_demo_membuat_tiga_akun_dan_aman_diulang(app, sesi_db, password_demo):
    runner = app.test_cli_runner()
    hasil = runner.invoke(args=["seed-demo"])
    assert hasil.exit_code == 0, hasil.output
    assert hasil.output.count("dibuat") == 3

    for peran, _nama, email, env in AKUN_DEMO:
        pengguna = sesi_db.scalar(select(Pengguna).where(Pengguna.email == email))
        assert pengguna.peran == peran
        assert pengguna.is_active
        assert pengguna.cek_password(password_demo[env])

    ulang = runner.invoke(args=["seed-demo"])
    assert ulang.exit_code == 0
    assert ulang.output.count("Lewati") == 3


def test_seed_demo_dengan_pasien_simulasi(app, sesi_db, password_demo):
    runner = app.test_cli_runner()
    hasil = runner.invoke(args=["seed-demo", "--dengan-pasien"])
    assert hasil.exit_code == 0, hasil.output

    nama = [nama for nama, *_ in PASIEN_SIMULASI]
    pasien = sesi_db.scalars(select(Pasien).where(Pasien.nama.in_(nama))).all()
    assert len(pasien) == len(PASIEN_SIMULASI)
    assert all(p.nik is None and p.no_telepon is None for p in pasien)
    assert sesi_db.query(Kunjungan).count() == len(PASIEN_SIMULASI)
    triase = sesi_db.scalars(select(Triase)).all()
    # Satu pasien sengaja belum ditriase supaya terlihat di daftar tunggu sebagai "belum ditriase",
    # dan satu pasien punya triase ulang.
    assert len(triase) == len(PASIEN_SIMULASI)
    assert {t.sumber_rekomendasi.value for t in triase} == {"model"}
    assert len({t.waktu_triase for t in triase}) == len(triase)
    assert [t.status_validasi for t in triase].count(StatusValidasi.MENUNGGU_REVIEW_DOKTER) == 1

    # Triase ulang Hendra levelnya naik, jadi muncul di peringatan.
    hendra = sorted((t for t in triase if t.kunjungan.pasien.nama == "Hendra Gunawan"), key=lambda t: t.waktu_triase)
    assert [t.jenis for t in hendra] == [JenisTriase.AWAL, JenisTriase.ULANG]
    assert URUTAN_LEVEL[hendra[1].risk_level] > URUTAN_LEVEL[hendra[0].risk_level]
    with app.test_request_context():
        dipantau = {p.nama_pasien for p in PeringatanService().kumpulkan()}
    assert "Hendra Gunawan" in dipantau

    ulang = runner.invoke(args=["seed-demo", "--dengan-pasien"])
    assert ulang.exit_code == 0
    assert ulang.output.count("Lewati pasien simulasi") == len(PASIEN_SIMULASI)
    assert sesi_db.query(Kunjungan).count() == len(PASIEN_SIMULASI)


def test_seed_demo_menolak_password_kosong(app, monkeypatch):
    for *_, env in AKUN_DEMO:
        monkeypatch.delenv(env, raising=False)
    monkeypatch.setenv("SEED_PASSWORD_ADMIN", "pendek")
    hasil = app.test_cli_runner().invoke(args=["seed-demo"])
    assert hasil.exit_code != 0
    assert "SEED_PASSWORD_ADMIN" in hasil.output
    assert "SEED_PASSWORD_DOKTER" in hasil.output


def test_normalisasi_email():
    assert normalisasi_email("  Dokter.Jaga@SmartTriage.DEMO\t") == "dokter.jaga@smarttriage.demo"
    with pytest.raises(ValueError, match="Format email tidak valid"):
        normalisasi_email("bukan email")


def test_email_login_maksimal_150_karakter():
    with pytest.raises(ValueError, match="150"):
        LoginRequest(email="a" * 140 + "@smarttriage.demo", password="x")


def test_pemformat_json():
    try:
        raise RuntimeError("gagal")
    except RuntimeError:
        catatan = logging.LogRecord("uji", logging.ERROR, __file__, 1, "pesan %s", ("satu",), exc_info=True)
        import sys

        catatan.exc_info = sys.exc_info()
    catatan.status = 500
    catatan.durasi_ms = 1.5
    data = json.loads(PemformatJson().format(catatan))
    assert data["pesan"] == "pesan satu"
    assert data["level"] == "ERROR"
    assert data["status"] == 500
    assert data["durasi_ms"] == 1.5
    assert "RuntimeError: gagal" in data["exc_info"]


def test_atur_logging_tidak_memasang_handler_ganda():
    root = logging.getLogger()
    sebelum = list(root.handlers)
    try:
        atur_logging()
        atur_logging()
        assert sum(isinstance(h, _HandlerSmartTriage) for h in root.handlers) == 1
    finally:
        for handler in list(root.handlers):
            if handler not in sebelum:
                root.removeHandler(handler)


def test_durasi_request_dicatat(client, caplog):
    with caplog.at_level(logging.INFO, logger="smarttriage.request"):
        client.get("/api/v1/health")
    catatan = [c for c in caplog.records if c.name == "smarttriage.request"][-1]
    assert catatan.status == 200
    assert catatan.path == "/api/v1/health"
    assert catatan.endpoint == "api_v1.health.health"
    assert catatan.durasi_ms >= 0
