"""Blueprint triase: input triase, detail triase, dan validasi hasilnya (FR-03, FR-05, FR-06)."""

from flask import jsonify
from flask_jwt_extended import get_current_user
from flask_openapi3 import APIBlueprint, Tag, validate_request

from app.ai.registry import model_registry
from app.middleware.auth import role_required
from app.models import Pengguna, Triase
from app.models.enums import Peran
from app.routes.dokumen import RESPONS_422, SEMUA_KANAL_ACCESS, respons_problem_doc
from app.services.konfigurasi_service import cache_konfigurasi
from app.services.triase_service import TriaseService, peringatan_triase, tanda_vital_triase
from app.services.validasi_service import ValidasiService
from app.utils.schemas import (
    KunjunganPath,
    PasienTriase,
    PenggunaRingkas,
    PenjelasanResponse,
    TandaVitalResponse,
    TriaseDetail,
    TriaseInput,
    TriasePath,
    ValidasiRequest,
)
from app.utils.waktu import WIB, usia_pasien

triase_bp = APIBlueprint(
    "triase",
    __name__,
    abp_tags=[Tag(name="Triase")],
    abp_security=SEMUA_KANAL_ACCESS,
    abp_responses=RESPONS_422,
)


def _ringkas(pengguna: Pengguna | None) -> PenggunaRingkas | None:
    return PenggunaRingkas.model_validate(pengguna) if pengguna is not None else None


def susun_detail(triase: Triase) -> TriaseDetail:
    pasien = triase.kunjungan.pasien
    tv = tanda_vital_triase(triase)
    return TriaseDetail(
        id_triase=triase.id_triase,
        id_kunjungan=triase.id_kunjungan,
        jenis=triase.jenis,
        pasien=PasienTriase(
            id_pasien=pasien.id_pasien,
            nama=pasien.nama,
            usia=usia_pasien(pasien.tanggal_lahir, pasien.perkiraan_usia, triase.waktu_triase.astimezone(WIB).date()),
            jenis_kelamin=pasien.jenis_kelamin,
        ),
        keluhan_utama=triase.keluhan_utama,
        gejala=triase.gejala,
        kategori_keluhan=triase.kategori_keluhan,
        skala_nyeri=triase.skala_nyeri,
        tingkat_kesadaran=triase.tingkat_kesadaran,
        tanda_vital=TandaVitalResponse(**tv.model_dump()),
        sumber_tanda_vital=triase.sumber_tanda_vital,
        risk_level=triase.risk_level,
        sumber_rekomendasi=triase.sumber_rekomendasi,
        penjelasan_ai=PenjelasanResponse.model_validate(triase.penjelasan_ai),
        status_validasi=triase.status_validasi,
        dibuat_oleh=_ringkas(triase.pembuat),
        divalidasi_oleh=_ringkas(triase.validator),
        waktu_triase=triase.waktu_triase,
        peringatan=peringatan_triase(triase),
        catatan_validasi_terakhir=TriaseService.catatan_validasi_terakhir(triase.id_triase),
    )


def _service() -> TriaseService:
    return TriaseService(model_registry(), cache_konfigurasi())


@triase_bp.post(
    "/kunjungan/<uuid:id_kunjungan>/triase",
    summary="Input triase dan rekomendasi risk level",
    description=(
        "Menyimpan triase berstatus menunggu validasi beserta rekomendasi risk level dan tiga faktor penjelas. "
        "Triase pertama pada kunjungan dicatat sebagai awal, berikutnya sebagai ulang. Nilai tanda vital yang "
        "tidak wajar dikembalikan di field peringatan tanpa menolak request."
    ),
    responses={201: TriaseDetail, **respons_problem_doc(401, 403, 404, 409)},
)
@role_required(Peran.PERAWAT)
@validate_request()
def buat_triase(path: KunjunganPath, body: TriaseInput):
    triase = _service().buat(path.id_kunjungan, body, get_current_user())
    return jsonify(susun_detail(triase).model_dump(mode="json")), 201


@triase_bp.get(
    "/triase/<uuid:id_triase>",
    summary="Detail triase beserta penjelasan rekomendasi",
    responses={200: TriaseDetail, **respons_problem_doc(401, 403, 404)},
)
@role_required(Peran.PERAWAT, Peran.DOKTER)
@validate_request()
def detail_triase(path: TriasePath):
    return jsonify(susun_detail(TriaseService.ambil(path.id_triase)).model_dump(mode="json"))


@triase_bp.post(
    "/triase/<uuid:id_triase>/validasi",
    summary="Menyetujui, mengoreksi, atau mengajukan review hasil triase",
    description=(
        "Perawat boleh menyetujui hasil non-kritis atau mengajukan review; dokter boleh menyetujui atau mengoreksi "
        "semua tingkat. Koreksi dan ajuan review wajib beralasan minimal 5 karakter. Triase yang sudah disetujui "
        "atau dikoreksi, sudah digantikan triase ulang, atau kunjungannya sudah selesai dibalas 409. Setiap aksi "
        "dicatat di log audit dalam transaksi yang sama."
    ),
    responses={200: TriaseDetail, **respons_problem_doc(401, 403, 404, 409)},
)
@role_required(Peran.PERAWAT, Peran.DOKTER)
@validate_request()
def validasi_triase(path: TriasePath, body: ValidasiRequest):
    triase = ValidasiService().validasi(path.id_triase, body, get_current_user())
    return jsonify(susun_detail(triase).model_dump(mode="json"))
