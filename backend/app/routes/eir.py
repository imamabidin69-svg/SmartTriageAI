"""Blueprint Eir untuk pasien zona hijau dan keluarganya, tanpa akun (FR-08, Desain 2.8).

Endpoint di sini tidak memakai JWT. POST /eir/sesi memakai token tautan dari kode QR, sedangkan endpoint
lain memakai token sesi di header X-Token-Eir yang hanya berlaku untuk satu sesi.
"""

from collections.abc import Callable
from functools import wraps

from flask import current_app, jsonify, request
from flask_openapi3 import APIBlueprint, Tag, validate_request

from app.ai.eir.agen import Balasan
from app.ai.eir.tautan import TokenEirTidakValidError, TokenSesiEir
from app.ai.registry import model_registry
from app.models.enums import PengisiEir
from app.routes.dokumen import RESPONS_422, respons_problem_doc
from app.services.eir_service import EirService
from app.utils.schemas import (
    BalasanEirResponse,
    BukaSesiEirRequest,
    PesanEirRequest,
    SesiEirDibuatResponse,
    SesiEirPath,
    UnggahSuara,
)

TOKEN_EIR = [{"tokenEir": []}]

eir_bp = APIBlueprint("eir", __name__, abp_tags=[Tag(name="Eir")], abp_responses=RESPONS_422)


@eir_bp.before_request
def _naikkan_batas_ukuran() -> None:
    # Batas umum request 1 MiB; khusus rekaman suara dinaikkan sedikit di atas 5 MB.
    if request.endpoint and request.endpoint.endswith("kirim_suara"):
        request.max_content_length = current_app.config["UKURAN_MAKS_REQUEST_SUARA"]


def token_sesi_wajib[**P, R](fungsi: Callable[P, R]) -> Callable[P, R]:
    """Memeriksa header X-Token-Eir sebelum isi request divalidasi, seperti role_required untuk staf."""

    @wraps(fungsi)
    def pembungkus(*args: P.args, **kwargs: P.kwargs) -> R:
        token = request.headers.get("X-Token-Eir")
        if not token:
            raise TokenEirTidakValidError("Header X-Token-Eir wajib dikirim.")
        umur = int(current_app.config["UMUR_TOKEN_EIR_DETIK"])
        TokenSesiEir(current_app.config["SECRET_KEY"], umur).baca(token, request.view_args["id_sesi"])
        return fungsi(*args, **kwargs)

    return pembungkus


def _service() -> EirService:
    return EirService(model_registry())


def _respons(balasan: Balasan, transkripsi: str | None = None):
    respons = BalasanEirResponse(
        status=balasan.status,
        pesan=balasan.pesan,
        jumlah_jawaban=balasan.jumlah_jawaban,
        boleh_selesai=balasan.boleh_selesai,
        transkripsi=transkripsi,
    )
    return jsonify(respons.model_dump(mode="json"))


@eir_bp.post(
    "/eir/sesi",
    summary="Memberi persetujuan dan membuka sesi Eir",
    description=(
        "Token diambil dari kode QR yang dibuat perawat (berlaku dua jam). Persetujuan wajib true. Respons berisi "
        "token sesi untuk header X-Token-Eir dan pertanyaan pertama Eir."
    ),
    responses={201: SesiEirDibuatResponse, **respons_problem_doc(401, 404, 409)},
)
@validate_request()
def buka_sesi(body: BukaSesiEirRequest):
    hasil = _service().buka_sesi(body.token, PengisiEir(body.pengisi))
    respons = SesiEirDibuatResponse(
        id_sesi=hasil.sesi.id_sesi, token_sesi=hasil.token_sesi, kedaluwarsa=hasil.kedaluwarsa, pesan=hasil.pesan
    )
    return jsonify(respons.model_dump(mode="json")), 201


@eir_bp.post(
    "/eir/sesi/<uuid:id_sesi>/pesan",
    summary="Mengirim jawaban ke Eir",
    description=(
        "Setiap jawaban diperiksa aturan tanda bahaya sebelum LLM dipanggil. Bila cocok, sesi dihentikan "
        "(status dihentikan), perawat mendapat peringatan, dan pesan berisi arahan menemui perawat. Setelah "
        "15 jawaban, atau saat jawaban sudah cukup, ringkasan dibuat otomatis (status selesai). Bila Groq tidak "
        "menjawab, respons 503 dan jawaban tetap tersimpan. Maksimal 20 pesan per menit per sesi."
    ),
    security=TOKEN_EIR,
    responses={200: BalasanEirResponse, **respons_problem_doc(401, 404, 409, 429, 503)},
)
@token_sesi_wajib
@validate_request()
def kirim_pesan(path: SesiEirPath, body: PesanEirRequest):
    return _respons(_service().kirim_pesan(path.id_sesi, body.teks))


@eir_bp.post(
    "/eir/sesi/<uuid:id_sesi>/suara",
    summary="Mengirim jawaban berupa rekaman suara (opsional)",
    description=(
        "Rekaman webm, ogg, mp3, m4a, atau wav maksimal 5 MB diubah ke teks dengan Whisper melalui Groq, lalu "
        "diproses seperti POST /pesan. Rekaman tidak disimpan. Hasil ubah suara ke teks dikirim di transkripsi."
    ),
    security=TOKEN_EIR,
    responses={200: BalasanEirResponse, **respons_problem_doc(401, 404, 409, 413, 429, 503)},
)
@token_sesi_wajib
@validate_request()
def kirim_suara(path: SesiEirPath, form: UnggahSuara):
    balasan, teks = _service().kirim_suara(path.id_sesi, form.berkas)
    return _respons(balasan, teks)


@eir_bp.post(
    "/eir/sesi/<uuid:id_sesi>/selesai",
    summary="Menyelesaikan sesi dan membuat ringkasan",
    description=(
        "Boleh dipanggil setelah minimal tujuh jawaban. Ringkasan dibuat LLM dengan JSON Schema, divalidasi, lalu "
        "disimpan sebagai draf untuk perawat (GET /kunjungan/{id}/ringkasan-eir). Bila Groq tidak menjawab, "
        "respons 503 dan sesi tetap berjalan sehingga bisa dicoba lagi."
    ),
    security=TOKEN_EIR,
    responses={200: BalasanEirResponse, **respons_problem_doc(401, 404, 409, 503)},
)
@token_sesi_wajib
@validate_request()
def selesai(path: SesiEirPath):
    return _respons(_service().selesai(path.id_sesi))
