import json
import logging

import pytest
from sqlalchemy import select

from app.cli import AKUN_DEMO
from app.models import Pengguna
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
