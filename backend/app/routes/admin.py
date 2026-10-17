"""Blueprint admin: kelola staf (FR-01) dan konfigurasi triase (FR-05). Log audit ada di blueprint rekap."""

from flask import jsonify
from flask_jwt_extended import get_current_user
from flask_openapi3 import APIBlueprint, Tag, validate_request

from app.ai.registry import model_registry
from app.middleware.auth import role_required
from app.models.enums import Peran
from app.routes.dokumen import RESPONS_422, SEMUA_KANAL_ACCESS, respons_problem_doc
from app.services.konfigurasi_service import KonfigurasiService, NilaiKonfigurasi, cache_konfigurasi
from app.services.staf_service import StafService
from app.utils.schemas import (
    DaftarStafResponse,
    KonfigurasiPatch,
    KonfigurasiResponse,
    StafDisimpanResponse,
    StafPatch,
    StafPath,
    StafQuery,
    StafRequest,
    StafResponse,
)

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


# ---------------------------------------------------------------- kelola staf (FR-01)


def _staf_disimpan(staf, password: str | None) -> dict:
    respons = StafDisimpanResponse(staf=StafResponse.model_validate(staf), password_sementara=password)
    return respons.model_dump(mode="json")


@admin_bp.get(
    "/staf",
    summary="Daftar akun staf",
    description="Semua staf diurutkan menurut nama, dengan filter opsional peran dan status aktif.",
    responses={200: DaftarStafResponse, **respons_problem_doc(401, 403)},
)
@role_required(Peran.ADMIN)
@validate_request()
def daftar_staf(query: StafQuery):
    items = [StafResponse.model_validate(s) for s in StafService().daftar(query.peran, query.aktif)]
    return jsonify(DaftarStafResponse(items=items).model_dump(mode="json"))


@admin_bp.post(
    "/staf",
    summary="Menambah akun staf",
    description=(
        "Server membuat password sementara 12 karakter yang dikirim sekali di respons. Sampaikan ke staf dan "
        "minta segera menggantinya lewat PATCH /auth/password."
    ),
    responses={201: StafDisimpanResponse, **respons_problem_doc(401, 403, 409)},
)
@role_required(Peran.ADMIN)
@validate_request()
def tambah_staf(body: StafRequest):
    staf, password = StafService().tambah(body, get_current_user())
    return jsonify(_staf_disimpan(staf, password)), 201


@admin_bp.patch(
    "/staf/<uuid:id_pengguna>",
    summary="Mengubah, menonaktifkan, atau mengatur ulang password staf",
    description=(
        "Hanya field yang dikirim yang diubah. is_active false menonaktifkan akun dan sesi yang sedang berjalan "
        "langsung ditolak. atur_ulang_password true membuat password sementara baru. Admin tidak bisa "
        "menonaktifkan atau mengubah peran dirinya sendiri, dan harus selalu ada satu admin aktif."
    ),
    responses={200: StafDisimpanResponse, **respons_problem_doc(401, 403, 404, 409)},
)
@role_required(Peran.ADMIN)
@validate_request()
def ubah_staf(path: StafPath, body: StafPatch):
    staf, password = StafService().ubah(path.id_pengguna, body, get_current_user())
    return jsonify(_staf_disimpan(staf, password))
