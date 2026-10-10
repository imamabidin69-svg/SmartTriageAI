from flask import current_app, jsonify
from flask_openapi3 import APIBlueprint, Tag

from app.services.health_service import HealthService
from app.utils.schemas import HealthResponse

health_bp = APIBlueprint("health", __name__, abp_tags=[Tag(name="Sistem")])


@health_bp.get(
    "/health",
    summary="Pemeriksaan kesehatan aplikasi",
    description="200 bila komponen wajib sehat (status ok atau degraded), 503 bila komponen wajib gagal.",
    # 422: None supaya flask-openapi3 tidak menambahkan skema error validasi; endpoint ini tanpa input.
    responses={200: HealthResponse, 503: HealthResponse, 422: None},
)
def health():
    hasil = HealthService(current_app.extensions["pemeriksa_kesehatan"]).periksa()
    return jsonify(hasil.model_dump()), 503 if hasil.status == "gagal" else 200
