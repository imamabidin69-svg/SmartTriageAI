"""Blueprint admin. Tahap ini berisi konfigurasi triase (FR-05); kelola staf dan log audit menyusul."""

from flask import jsonify
from flask_jwt_extended import get_current_user
from flask_openapi3 import APIBlueprint, Tag, validate_request

from app.ai.registry import model_registry
from app.middleware.auth import role_required
from app.models.enums import Peran
from app.routes.dokumen import RESPONS_422, SEMUA_KANAL_ACCESS, respons_problem_doc
from app.services.konfigurasi_service import KonfigurasiService, NilaiKonfigurasi, cache_konfigurasi
from app.utils.schemas import KonfigurasiPatch, KonfigurasiResponse

admin_bp = APIBlueprint(
    "admin",
    __name__,
    url_prefix="/admin",
    abp_tags=[Tag(name="Admin")],
    abp_security=SEMUA_KANAL_ACCESS,
    abp_responses=RESPONS_422,
)


def _service() -> KonfigurasiService:
    return KonfigurasiService(model_registry(), cache_konfigurasi())


def _respons(nilai: NilaiKonfigurasi) -> dict:
    respons = KonfigurasiResponse(
        versi_model=nilai.versi_model,
        ambang_kritis=nilai.ambang_kritis,
        ambang_tinggi=nilai.ambang_tinggi,
        ambang_sedang=nilai.ambang_sedang,
        batas_tunggu_tinggi=nilai.batas_tunggu_tinggi,
        batas_tunggu_sedang=nilai.batas_tunggu_sedang,
        batas_tunggu_rendah=nilai.batas_tunggu_rendah,
        ambang_keyakinan=float(nilai.ambang_keyakinan),
        versi_model_termuat=model_registry().versi_model,
    )
    return respons.model_dump(mode="json")


@admin_bp.get(
    "/konfigurasi",
    summary="Membaca konfigurasi triase",
    responses={200: KonfigurasiResponse, **respons_problem_doc(401, 403)},
)
@role_required(Peran.ADMIN)
def ambil_konfigurasi():
    return jsonify(_respons(_service().ambil()))


@admin_bp.patch(
    "/konfigurasi",
    summary="Mengubah sebagian konfigurasi triase",
    description=(
        "Hanya field yang dikirim yang diubah. Setiap perubahan dicatat di log audit. Ambang harus berurutan "
        "(kritis > tinggi > sedang) dan batas tunggu tidak menurun (tinggi <= sedang <= rendah)."
    ),
    responses={200: KonfigurasiResponse, **respons_problem_doc(401, 403)},
)
@role_required(Peran.ADMIN)
@validate_request()
def ubah_konfigurasi(body: KonfigurasiPatch):
    return jsonify(_respons(_service().ubah(body, get_current_user())))
