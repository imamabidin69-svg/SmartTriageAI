"""Blueprint pemindaian: membaca angka dari foto layar alat tanda vital (FR-04)."""

from flask import current_app, jsonify, request
from flask_jwt_extended import get_current_user
from flask_openapi3 import APIBlueprint, Tag, validate_request

from app.ai.registry import model_registry
from app.middleware.auth import role_required
from app.models.enums import Peran
from app.routes.dokumen import RESPONS_422, SEMUA_KANAL_ACCESS, respons_problem_doc
from app.services.konfigurasi_service import cache_konfigurasi
from app.services.pemindaian_service import PemindaianService
from app.utils.schemas import HasilPemindaianResponse, UnggahFoto

pemindaian_bp = APIBlueprint(
    "pemindaian",
    __name__,
    abp_tags=[Tag(name="Pemindaian")],
    abp_security=SEMUA_KANAL_ACCESS,
    abp_responses=RESPONS_422,
)


@pemindaian_bp.before_request
def _naikkan_batas_ukuran() -> None:
    # Batas umum request 1 MiB; khusus unggah foto dinaikkan sedikit di atas 5 MB.
    request.max_content_length = current_app.config["UKURAN_MAKS_REQUEST_FOTO"]


@pemindaian_bp.post(
    "/pemindaian",
    summary="Membaca angka dari foto layar alat",
    description=(
        "Body multipart berisi jenis_alat dan berkas (foto JPEG atau PNG maksimal 5 MB). Foto hanya diproses di "
        "memori lalu dibuang. Kolom diisi bila keyakinan model mencapai ambang konfigurasi dan nilainya wajar; "
        "selebihnya null untuk diisi manual. Kirim id_pemindaian lewat form triase setelah nilai dikonfirmasi."
    ),
    responses={200: HasilPemindaianResponse, **respons_problem_doc(401, 403, 413)},
)
@role_required(Peran.PERAWAT)
@validate_request()
def pindai(form: UnggahFoto):
    service = PemindaianService(
        model_registry().pembaca_layar, cache_konfigurasi(), current_app.config["UKURAN_MAKS_FOTO"]
    )
    hasil = service.pindai(form.berkas, form.jenis_alat, get_current_user())
    respons = HasilPemindaianResponse(
        id_pemindaian=hasil.pemindaian.id_pemindaian,
        jenis_alat=form.jenis_alat,
        nilai=hasil.nilai,
        keyakinan=hasil.keyakinan,
        kolom_kosong=hasil.kolom_kosong,
        pembaca_tersedia=hasil.pembaca_tersedia,
    )
    return jsonify(respons.model_dump(mode="json"))
