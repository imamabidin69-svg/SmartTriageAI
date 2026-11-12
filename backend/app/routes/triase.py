"""Blueprint triase: observasi ICU, detail penilaian, persetujuan dokter, dan riwayat (FR-03, FR-05, FR-06, FR-09).

Path /triase dipertahankan dari SKPL. Di ICU satu "triase" adalah satu observasi beserta penilaian prioritasnya.
"""

from flask import jsonify
from flask_jwt_extended import get_current_user
from flask_openapi3 import APIBlueprint, Tag, validate_request

from app.ai.registry import model_registry
from app.middleware.auth import role_required
from app.models import Pengguna, Triase
from app.models.enums import Peran
from app.routes.dokumen import RESPONS_422, SEMUA_KANAL_ACCESS, respons_problem_doc
from app.services.konfigurasi_service import cache_konfigurasi
from app.services.riwayat_service import RiwayatService
from app.services.triase_service import TriaseService, peringatan_triase, tanda_vital_triase
from app.services.validasi_service import ValidasiService
from app.utils.schemas import (
    HalamanQuery,
    HasilLabResponse,
    ItemRiwayat,
    KunjunganPath,
    KunjunganRiwayat,
    PasienPath,
    PasienTriase,
    PenggunaRingkas,
    PenjelasanResponse,
    RiwayatResponse,
    TandaVitalResponse,
    TriaseDetail,
    TriaseInput,
    TriasePath,
    ValidasiRequest,
)
from app.utils.waktu import WIB, hari_ini, usia_pasien

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
    sebelumnya = TriaseService.observasi_terakhir(triase.id_kunjungan, sebelum=triase)
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
        nomor_bed=triase.kunjungan.nomor_bed,
        status_kunjungan=triase.kunjungan.status,
        tingkat_kesadaran=triase.tingkat_kesadaran,
        oksigen_tambahan=triase.oksigen_tambahan,
        tanda_vital=TandaVitalResponse(**tv.model_dump()),
        lab=HasilLabResponse.model_validate(triase, from_attributes=True),
        ventilator=triase.ventilator,
        vasopresor=triase.vasopresor,
        catatan=triase.catatan,
        sumber_tanda_vital=triase.sumber_tanda_vital,
        skor_news2=triase.skor_news2,
        peluang_perburukan=triase.peluang_perburukan,
        level_sebelumnya=None if sebelumnya is None else sebelumnya.risk_level,
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
    summary="Mencatat observasi pasien ICU dan menilai prioritasnya",
    description=(
        "Menghitung skor NEWS2 dan peluang perburukan 6 jam dari model Random Forest, lalu memakai level yang "
        "lebih tinggi dari keduanya. Observasi pertama (awal) dan observasi yang levelnya naik dibanding level "
        "final terakhir berstatus menunggu persetujuan dokter; selain itu langsung berstatus tercatat. Nilai yang "
        "tidak wajar dikembalikan di field peringatan tanpa menolak request. Pasien yang sudah keluar ICU dibalas 409."
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
    summary="Detail observasi beserta penjelasan penilaian",
    responses={200: TriaseDetail, **respons_problem_doc(401, 403, 404)},
)
@role_required(Peran.PERAWAT, Peran.DOKTER)
@validate_request()
def detail_triase(path: TriasePath):
    return jsonify(susun_detail(TriaseService.ambil(path.id_triase)).model_dump(mode="json"))


@triase_bp.post(
    "/triase/<uuid:id_triase>/validasi",
    summary="Persetujuan dokter: menyetujui, mengoreksi, atau mengajukan review",
    description=(
        "Hanya dokter yang boleh menyetujui atau mengoreksi level; perawat hanya boleh mengajukan review. Koreksi "
        "dan ajuan review wajib beralasan minimal 5 karakter. Penilaian yang sudah final (disetujui, dikoreksi, "
        "atau tercatat), sudah digantikan observasi yang lebih baru, atau pasiennya sudah keluar ICU dibalas 409. "
        "Setiap aksi dicatat di log audit dalam transaksi yang sama."
    ),
    responses={200: TriaseDetail, **respons_problem_doc(401, 403, 404, 409)},
)
@role_required(Peran.PERAWAT, Peran.DOKTER)
@validate_request()
def validasi_triase(path: TriasePath, body: ValidasiRequest):
    triase = ValidasiService().validasi(path.id_triase, body, get_current_user())
    return jsonify(susun_detail(triase).model_dump(mode="json"))


@triase_bp.get(
    "/pasien/<uuid:id_pasien>/riwayat",
    summary="Riwayat observasi pasien",
    description=(
        "Observasi dari semua masa rawat ICU pasien, terbaru lebih dulu. Halaman berikutnya diambil dengan "
        "mengirim kursor_berikutnya sebagai parameter kursor. NIK dan nomor telepon tidak dikirim."
    ),
    responses={200: RiwayatResponse, **respons_problem_doc(401, 403, 404)},
)
@role_required(Peran.PERAWAT, Peran.DOKTER)
@validate_request()
def riwayat_pasien(path: PasienPath, query: HalamanQuery):
    halaman = RiwayatService().ambil(path.id_pasien, query.kursor, query.ukuran)
    pasien = halaman.pasien
    items = [
        ItemRiwayat(
            id_triase=t.id_triase,
            jenis=t.jenis,
            waktu_triase=t.waktu_triase,
            skor_news2=t.skor_news2,
            peluang_perburukan=t.peluang_perburukan,
            risk_level=t.risk_level,
            sumber_rekomendasi=t.sumber_rekomendasi,
            status_validasi=t.status_validasi,
            tanda_vital=TandaVitalResponse(**tanda_vital_triase(t).model_dump()),
            dibuat_oleh=_ringkas(t.pembuat),
            divalidasi_oleh=_ringkas(t.validator),
            kunjungan=KunjunganRiwayat.model_validate(t.kunjungan, from_attributes=True),
        )
        for t in halaman.items
    ]
    respons = RiwayatResponse(
        pasien=PasienTriase(
            id_pasien=pasien.id_pasien,
            nama=pasien.nama,
            usia=usia_pasien(pasien.tanggal_lahir, pasien.perkiraan_usia, hari_ini()),
            jenis_kelamin=pasien.jenis_kelamin,
        ),
        items=items,
        kursor_berikutnya=halaman.kursor_berikutnya,
    )
    return jsonify(respons.model_dump(mode="json"))
