"""Pendaftaran blueprint di bawah prefiks /api/v1."""

from flask_openapi3 import APIBlueprint, OpenAPI

from app.routes.admin import admin_bp
from app.routes.antrean import antrean_bp
from app.routes.auth import auth_bp
from app.routes.health import health_bp
from app.routes.kunjungan import kunjungan_bp
from app.routes.triase import triase_bp

PREFIKS_API = "/api/v1"


def daftarkan_rute(app: OpenAPI) -> None:
    api_v1 = APIBlueprint("api_v1", __name__, url_prefix=PREFIKS_API)
    for blueprint in (auth_bp, health_bp, admin_bp, kunjungan_bp, triase_bp, antrean_bp):
        api_v1.register_api(blueprint)
    app.register_api(api_v1)
