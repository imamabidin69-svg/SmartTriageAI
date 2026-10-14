"""Blueprint kunjungan: pencarian pasien, registrasi kunjungan, dan status kunjungan (FR-02, FR-07)."""

from flask import jsonify
from flask_jwt_extended import get_current_user
from flask_openapi3 import APIBlueprint, Tag, validate_request

from app.middleware.auth import role_required
from app.models.enums import Peran, StatusKunjungan
from app.routes.dokumen import RESPONS_422, SEMUA_KANAL_ACCESS, respons_problem_doc
from app.services.kunjungan_service import KunjunganService, samarkan_nik, usia
from app.utils.schemas import (
    CariPasienQuery,
    DaftarPasienResponse,
    KunjunganDibuatResponse,
    KunjunganPath,
    PasienRingkas,
    RegistrasiRequest,
    StatusKunjunganRequest,
    StatusKunjunganResponse,
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
    description=(
        "Potongan nama (tanpa membedakan huruf besar) atau NIK lengkap 16 digit. Maksimal 20 hasil. "
        "Pencarian NIK yang tidak menemukan pasien dibatasi 30 kali per 15 menit untuk setiap akun."
    ),
    responses={200: DaftarPasienResponse, **respons_problem_doc(401, 403, 429)},
)
@role_required(Peran.PERAWAT, Peran.DOKTER)
@validate_request()
def cari_pasien(query: CariPasienQuery):
    hasil = KunjunganService().cari_pasien_oleh(query.q, get_current_user())
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


@kunjungan_bp.patch(
    "/kunjungan/<uuid:id_kunjungan>/status",
    summary="Menandai pasien mulai diperiksa atau selesai",
    description=(
        "Dokter mengubah status menunggu ke ditangani (pasien keluar dari daftar tunggu), ditangani ke selesai, "
        "atau menunggu ke selesai untuk pasien yang batal diperiksa. Perubahan lain dibalas 409."
    ),
    responses={200: StatusKunjunganResponse, **respons_problem_doc(401, 403, 404, 409)},
)
@role_required(Peran.DOKTER)
@validate_request()
def ubah_status(path: KunjunganPath, body: StatusKunjunganRequest):
    kunjungan = KunjunganService().ubah_status(path.id_kunjungan, StatusKunjungan(body.status))
    respons = StatusKunjunganResponse(
        id_kunjungan=kunjungan.id_kunjungan, status=kunjungan.status, waktu_ditangani=kunjungan.waktu_ditangani
    )
    return jsonify(respons.model_dump(mode="json"))
