"""Application factory SmartTriage AI."""

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from flask_openapi3 import Info, OpenAPI
from werkzeug.middleware.proxy_fix import ProxyFix

from app.ai.registry import ModelRegistry
from app.cli import daftarkan_perintah
from app.config import buat_konfigurasi, validasi_konfigurasi
from app.extensions import db, jwt, limiter, migrate
from app.middleware import auth as _loader_jwt  # noqa: F401  (mendaftarkan loader JWT)
from app.middleware.keamanan import pasang_header_keamanan
from app.middleware.pengukur_durasi import pasang_pengukur_durasi
from app.routes import daftarkan_rute
from app.routes.dokumen import SKEMA_KEAMANAN
from app.services.health_service import (
    PemeriksaDatabase,
    PemeriksaHakAksesLogAudit,
    PemeriksaModel,
    PemeriksaPembacaLayar,
)
from app.services.konfigurasi_service import CacheKonfigurasi
from app.utils.errors import ProblemDetails, daftarkan_penangan_error, respons_validasi_gagal
from app.utils.log import atur_logging
from app.utils.penyedia_json import PenyediaJson
from app.utils.request import RequestTanpaBerkasSementara

DIREKTORI_MIGRASI = str(Path(__file__).resolve().parent.parent / "migrations")


def create_app(konfigurasi: Mapping[str, Any] | None = None) -> OpenAPI:
    """Membuat aplikasi Flask.

    `konfigurasi` menimpa nilai dari environment variable; dipakai terutama oleh tes.
    Lingkungan dipilih lewat APP_ENV (development, testing, production) dan bawaannya production,
    supaya environment variable yang terlupa tidak membuat aplikasi berjalan dengan setelan longgar.
    """
    timpaan = dict(konfigurasi or {})
    nama_env = timpaan.get("APP_ENV") or os.environ.get("APP_ENV") or "production"
    nilai = buat_konfigurasi(nama_env)
    nilai.update(timpaan)
    validasi_konfigurasi(nilai)

    app = OpenAPI(
        __name__,
        info=Info(title="SmartTriage AI API", version="1.0.0"),
        security_schemes=SKEMA_KEAMANAN,
        doc_ui=nilai["DOKUMENTASI_API_AKTIF"],
        doc_prefix=nilai["PREFIKS_DOKUMENTASI"],
        validation_error_status=422,
        validation_error_model=ProblemDetails,
        validation_error_callback=respons_validasi_gagal,
    )
    app.config.from_mapping(nilai)
    app.json = PenyediaJson(app)
    app.request_class = RequestTanpaBerkasSementara

    if not app.testing:
        atur_logging()

    jumlah_proxy = int(app.config["JUMLAH_PROXY"])
    if jumlah_proxy:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=jumlah_proxy, x_proto=jumlah_proxy)

    db.init_app(app)
    migrate.init_app(app, db, directory=DIREKTORI_MIGRASI, compare_type=True, render_as_batch=False)
    jwt.init_app(app)
    limiter.init_app(app)

    daftarkan_penangan_error(app)
    pasang_header_keamanan(app)
    pasang_pengukur_durasi(app)
    daftarkan_rute(app)
    daftarkan_perintah(app)

    # Model dimuat sekali per proses (Desain Gambar 3.6). Gagal dimuat berarti aturan cadangan dipakai.
    registry = ModelRegistry()
    registry.muat(app.config["MODEL_RF_PATH"])
    registry.muat_pembaca_layar(app.config["MODEL_YOLO_PATH"], app.config["PEMBACA_LAYAR"])
    app.extensions["model_registry"] = registry
    app.extensions["cache_konfigurasi"] = CacheKonfigurasi(app.config["CACHE_KONFIGURASI_DETIK"])

    # Daftar komponen yang diperiksa GET /api/v1/health. Tahap Eir menambah Groq.
    app.extensions["pemeriksa_kesehatan"] = [
        PemeriksaDatabase(),
        PemeriksaHakAksesLogAudit(),
        PemeriksaModel(registry),
        PemeriksaPembacaLayar(registry),
    ]
    return app
