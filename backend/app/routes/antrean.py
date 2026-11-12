"""Blueprint antrean: papan prioritas ICU dan peringatan, dipanggil aplikasi setiap 15 detik (FR-07)."""

from datetime import UTC

from flask import jsonify
from flask_openapi3 import APIBlueprint, Tag

from app.middleware.auth import role_required
from app.models.enums import Peran
from app.routes.dokumen import SEMUA_KANAL_ACCESS, respons_problem_doc
from app.services.daftar_tunggu_service import DaftarTungguService, ItemDaftarTunggu
from app.services.konfigurasi_service import cache_konfigurasi
from app.services.peringatan_service import PeringatanService
from app.utils.schemas import (
    DaftarPeringatanResponse,
    DaftarTungguResponse,
    ItemPeringatan,
    PasienPeringatan,
    PasienTriase,
    TriaseTerakhir,
)
from app.utils.schemas import ItemDaftarTunggu as ItemDaftarTungguResponse
from app.utils.waktu import sekarang

antrean_bp = APIBlueprint(
    "antrean",
    __name__,
    abp_tags=[Tag(name="Antrean")],
    abp_security=SEMUA_KANAL_ACCESS,
)


def _item_respons(item: ItemDaftarTunggu) -> ItemDaftarTungguResponse:
    triase = item.triase_terakhir
    return ItemDaftarTungguResponse(
        id_kunjungan=item.kunjungan.id_kunjungan,
        pasien=PasienTriase(
            id_pasien=item.pasien.id_pasien,
            nama=item.pasien.nama,
            usia=item.usia,
            jenis_kelamin=item.pasien.jenis_kelamin,
        ),
        nomor_bed=item.kunjungan.nomor_bed,
        diagnosis_masuk=item.kunjungan.diagnosis_masuk,
        status=item.kunjungan.status,
        waktu_datang=item.kunjungan.waktu_datang,
        triase_terakhir=None if triase is None else TriaseTerakhir.model_validate(triase, from_attributes=True),
        lama_menunggu_menit=item.lama_menunggu,
        batas_tunggu_menit=item.batas_tunggu,
        status_tanda=item.status_tanda,
        menunggu_validasi=item.menunggu_validasi,
        review_diajukan=item.review_diajukan,
        ringkasan_eir_siap=item.ringkasan_eir_siap,
    )


@antrean_bp.get(
    "/daftar-tunggu",
    summary="Papan prioritas pasien ICU",
    description=(
        "Semua pasien yang belum keluar ICU beserta penilaian terakhirnya, sudah diurutkan menurut prioritas "
        "penanganan: Kritis, belum dinilai, Tinggi, Sedang, Rendah; di level yang sama yang menunggu persetujuan "
        "dokter dan yang observasinya terlambat lebih dulu, lalu peluang perburukan dan skor NEWS2 tertinggi. "
        "Pasien yang sedang menjalani tindakan ditaruh paling bawah. Lama dihitung sejak observasi terakhir dan "
        "dibandingkan dengan interval observasi level tersebut."
    ),
    responses={200: DaftarTungguResponse, **respons_problem_doc(401, 403)},
)
@role_required(Peran.PERAWAT, Peran.DOKTER)
def daftar_tunggu():
    waktu = sekarang()
    items = DaftarTungguService(cache_konfigurasi().ambil()).susun(waktu)
    # Ditulis dalam UTC seperti waktu lain yang dibaca dari basis data.
    respons = DaftarTungguResponse(items=[_item_respons(item) for item in items], waktu_server=waktu.astimezone(UTC))
    return jsonify(respons.model_dump(mode="json"))


@antrean_bp.get(
    "/peringatan",
    summary="Peringatan persetujuan dokter, observasi terlambat, dan informasi penting Eir",
    description=(
        "Penilaian awal atau kenaikan level yang belum disetujui dokter, observasi yang melewati intervalnya, dan "
        "informasi penting dari keluarga lewat Eir yang belum diikuti observasi baru. Hanya pasien yang masih di ICU."
    ),
    responses={200: DaftarPeringatanResponse, **respons_problem_doc(401, 403)},
)
@role_required(Peran.PERAWAT, Peran.DOKTER)
def peringatan():
    items = [
        ItemPeringatan(
            jenis=p.jenis,
            id_kunjungan=p.id_kunjungan,
            id_triase=p.id_triase,
            id_sesi=p.id_sesi,
            pasien=PasienPeringatan(id_pasien=p.id_pasien, nama=p.nama_pasien),
            risk_level=p.risk_level,
            alasan=p.alasan,
            waktu=p.waktu,
        )
        for p in PeringatanService(cache_konfigurasi().ambil()).kumpulkan(sekarang())
    ]
    return jsonify(DaftarPeringatanResponse(items=items).model_dump(mode="json"))
