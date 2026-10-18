from pathlib import Path

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
    # .env pengembang boleh berisi mode tiruan untuk mencoba di Swagger; di sini harus memakai bawaan production.
    monkeypatch.delenv("PEMBACA_LAYAR", raising=False)
    monkeypatch.delenv("LLM_EIR", raising=False)
    # Pembaca dan LLM tiruan dari konfigurasi tes tidak boleh dipakai di production, jadi ikut dibuang.
    konfigurasi = {k: v for k, v in konfigurasi_app.items() if k not in ("APP_ENV", "PEMBACA_LAYAR", "LLM_EIR")}
    aplikasi = create_app(konfigurasi)
    assert aplikasi.config["APP_ENV"] == "production"
    assert aplikasi.config["JWT_COOKIE_SECURE"] is True
    assert not isinstance(aplikasi.wsgi_app, ProxyFix)


def test_proxyfix_aktif_bila_ada_proxy_tepercaya(konfigurasi_app):
    aplikasi = create_app({**konfigurasi_app, "JUMLAH_PROXY": 1})
    assert isinstance(aplikasi.wsgi_app, ProxyFix)


def test_model_rf_path_relatif_dihitung_dari_folder_backend(monkeypatch):
    from app.config import DIREKTORI_BACKEND

    monkeypatch.setenv("MODEL_RF_PATH", "app/ai/artefak/lain.joblib")
    assert buat_konfigurasi("testing")["MODEL_RF_PATH"] == str(DIREKTORI_BACKEND / "app/ai/artefak/lain.joblib")
    # Path absolut dibuat sesuai sistem operasi: /opt/... di Linux, F:\opt\... di Windows.
    mutlak = str(Path(DIREKTORI_BACKEND.anchor) / "opt" / "model" / "rf.joblib")
    monkeypatch.setenv("MODEL_RF_PATH", mutlak)
    assert buat_konfigurasi("testing")["MODEL_RF_PATH"] == mutlak
    monkeypatch.delenv("MODEL_RF_PATH")
    assert buat_konfigurasi("testing")["MODEL_RF_PATH"].endswith("model_rf.joblib")


def test_model_yolo_path_dan_mode_pembaca_dari_environment(monkeypatch):
    from app.config import DIREKTORI_BACKEND

    monkeypatch.setenv("MODEL_YOLO_PATH", "app/ai/artefak/lain.onnx")
    monkeypatch.setenv("PEMBACA_LAYAR", " Tiruan ")
    nilai = buat_konfigurasi("development")
    assert nilai["MODEL_YOLO_PATH"] == str(DIREKTORI_BACKEND / "app/ai/artefak/lain.onnx")
    assert nilai["PEMBACA_LAYAR"] == "tiruan"
    monkeypatch.delenv("MODEL_YOLO_PATH")
    monkeypatch.delenv("PEMBACA_LAYAR")
    nilai = buat_konfigurasi("development")
    assert nilai["MODEL_YOLO_PATH"].endswith("yolo_digit.onnx")
    assert nilai["PEMBACA_LAYAR"] == "onnx"


@pytest.mark.parametrize("app_env", ["development", "testing"])
def test_pembaca_tiruan_boleh_di_development(app_env):
    validasi_konfigurasi(konfigurasi_valid(PEMBACA_LAYAR="tiruan", APP_ENV=app_env))


@pytest.mark.parametrize(
    ("ubah", "pesan"),
    [
        ({"PEMBACA_LAYAR": "tiruan", "APP_ENV": "production"}, "hanya boleh dipakai di development"),
        ({"PEMBACA_LAYAR": "yolo"}, "PEMBACA_LAYAR harus onnx atau tiruan"),
    ],
)
def test_pembaca_layar_tidak_valid_ditolak(ubah, pesan):
    with pytest.raises(KonfigurasiTidakValidError, match=pesan):
        validasi_konfigurasi(konfigurasi_valid(**ubah))


def test_konfigurasi_eir_dari_environment(monkeypatch):
    from app.config import DIREKTORI_BACKEND

    monkeypatch.setenv("LLM_EIR", " Tiruan ")
    monkeypatch.setenv("GROQ_API_KEY", " gsk_contoh ")
    monkeypatch.setenv("PANDUAN_EIR_PATH", "panduan_lain")
    nilai = buat_konfigurasi("development")
    assert (nilai["LLM_EIR"], nilai["GROQ_API_KEY"]) == ("tiruan", "gsk_contoh")
    assert nilai["PANDUAN_EIR_PATH"] == str(DIREKTORI_BACKEND / "panduan_lain")
    for nama in ("LLM_EIR", "GROQ_API_KEY", "PANDUAN_EIR_PATH"):
        monkeypatch.delenv(nama)
    nilai = buat_konfigurasi("development")
    assert (nilai["LLM_EIR"], nilai["GROQ_API_KEY"]) == ("groq", None)
    assert nilai["PANDUAN_EIR_PATH"].endswith("panduan")


@pytest.mark.parametrize(
    ("ubah", "pesan"),
    [
        ({"LLM_EIR": "tiruan", "APP_ENV": "production"}, "LLM_EIR=tiruan hanya boleh dipakai di development"),
        ({"LLM_EIR": "openai"}, "LLM_EIR harus groq atau tiruan"),
    ],
)
def test_llm_eir_tidak_valid_ditolak(ubah, pesan):
    with pytest.raises(KonfigurasiTidakValidError, match=pesan):
        validasi_konfigurasi(konfigurasi_valid(**ubah))


def test_llm_eir_tiruan_boleh_di_development():
    validasi_konfigurasi(konfigurasi_valid(LLM_EIR="tiruan", APP_ENV="development"))
