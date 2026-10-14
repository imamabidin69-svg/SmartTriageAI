"""Blueprint kunjungan: pencarian pasien dan registrasi kunjungan (FR-02)."""

from flask import jsonify
from flask_jwt_extended import get_current_user
from flask_openapi3 import APIBlueprint, Tag, validate_request

from app.middleware.auth import role_required
from app.models.enums import Peran
from app.routes.dokumen import RESPONS_422, SEMUA_KANAL_ACCESS, respons_problem_doc
from app.services.kunjungan_service import KunjunganService, samarkan_nik, usia
from app.utils.schemas import (
    CariPasienQuery,
    DaftarPasienResponse,
    KunjunganDibuatResponse,
    PasienRingkas,
    RegistrasiRequest,
)

kunjungan_bp = APIBlueprint(
    "kunjungan",
    __name__,
    abp_tags=[Tag(name="Kunjungan")],
    abp_security=SEMUA_KANAL_ACCESS,
    abp_responses=RESPONS_422,
)


@kunjungan_bp.get(
    "/pasien",
    summary="Mencari pasien lama",
    description="Potongan nama (tanpa membedakan huruf besar) atau NIK lengkap 16 digit. Maksimal 20 hasil.",
    responses={200: DaftarPasienResponse, **respons_problem_doc(401, 403)},
)
@role_required(Peran.PERAWAT, Peran.DOKTER)
@validate_request()
def cari_pasien(query: CariPasienQuery):
    hasil = KunjunganService().cari_pasien(query.q)
    items = [
        PasienRingkas(
            id_pasien=h.pasien.id_pasien,
            nama=h.pasien.nama,
            jenis_kelamin=h.pasien.jenis_kelamin,
            tanggal_lahir=h.pasien.tanggal_lahir,
            perkiraan_usia=h.pasien.perkiraan_usia,
            usia=usia(h.pasien),
            nik_tersamar=samarkan_nik(h.pasien.nik),
            id_kunjungan_aktif=h.id_kunjungan_aktif,
        )
        for h in hasil
    ]
    return jsonify(DaftarPasienResponse(items=items).model_dump(mode="json"))


@kunjungan_bp.post(
    "/kunjungan",
    summary="Registrasi singkat dan pembuatan kunjungan",
    description=(
        "Pilih pasien lama lewat id_pasien, atau isi identitas pasien baru. Pasien dengan NIK yang sudah "
        "terdaftar dipakai ulang bila nama dan jenis kelaminnya sama."
    ),
    responses={201: KunjunganDibuatResponse, **respons_problem_doc(401, 403, 409)},
)
@role_required(Peran.PERAWAT)
@validate_request()
def registrasi(body: RegistrasiRequest):
    hasil = KunjunganService().daftar(body, get_current_user())
    kunjungan = hasil.kunjungan
    respons = KunjunganDibuatResponse(
        id_kunjungan=kunjungan.id_kunjungan,
        id_pasien=kunjungan.id_pasien,
        pasien_baru=hasil.pasien_baru,
        status=kunjungan.status,
        waktu_datang=kunjungan.waktu_datang,
    )
    return jsonify(respons.model_dump(mode="json")), 201
