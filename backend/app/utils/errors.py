"""Respons error berformat Problem Details (RFC 9457) dengan pesan berbahasa Indonesia.

Semua error API, termasuk validasi, autentikasi, dan batas percobaan login, dikirim dengan
Content-Type application/problem+json supaya web admin dan aplikasi Flutter cukup punya
satu cara menampilkan pesan, termasuk menyorot field yang salah.
"""

import json
import logging
from decimal import Decimal
from typing import Any, ClassVar

from flask import Flask, Response, request
from flask_limiter.errors import RateLimitExceeded
from pydantic import BaseModel, ValidationError
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)

MIMETYPE_PROBLEM = "application/problem+json"
PREFIKS_KODE_KUSTOM = "kustom_"


class Tipe:
    """Nilai field `type` Problem Details. Klien memakai nilai ini untuk menentukan tindakan."""

    VALIDASI = "urn:smarttriage:problem:validasi"
    JSON_TIDAK_VALID = "urn:smarttriage:problem:json-tidak-valid"
    TIDAK_TERAUTENTIKASI = "urn:smarttriage:problem:tidak-terautentikasi"
    KREDENSIAL_SALAH = "urn:smarttriage:problem:kredensial-salah"
    AKUN_NONAKTIF = "urn:smarttriage:problem:akun-nonaktif"
    TOKEN_TIDAK_VALID = "urn:smarttriage:problem:token-tidak-valid"  # noqa: S105
    TOKEN_KEDALUWARSA = "urn:smarttriage:problem:token-kedaluwarsa"  # noqa: S105
    SESI_BERAKHIR = "urn:smarttriage:problem:sesi-berakhir"
    AKSES_DITOLAK = "urn:smarttriage:problem:akses-ditolak"
    TIDAK_DITEMUKAN = "urn:smarttriage:problem:tidak-ditemukan"
    METODE_TIDAK_DIIZINKAN = "urn:smarttriage:problem:metode-tidak-diizinkan"
    KONFLIK = "urn:smarttriage:problem:konflik"
    TERLALU_BESAR = "urn:smarttriage:problem:isi-terlalu-besar"
    TERLALU_BANYAK_PERCOBAAN = "urn:smarttriage:problem:terlalu-banyak-percobaan"
    KESALAHAN_SERVER = "urn:smarttriage:problem:kesalahan-server"
    PERMINTAAN_TIDAK_VALID = "urn:smarttriage:problem:permintaan-tidak-valid"


class FieldError(BaseModel):
    field: str
    pesan: str


class ProblemDetails(BaseModel):
    """Bentuk respons error untuk dokumentasi OpenAPI."""

    type: str
    title: str
    status: int
    detail: str | None = None
    instance: str | None = None
    errors: list[FieldError] | None = None


class AplikasiError(Exception):
    """Error yang sudah diketahui bentuk responsnya, dilempar oleh service.

    `errors` berisi pesan per field (dipakai error validasi dari service), sedangkan `ekstra`
    ditambahkan sebagai anggota tambahan Problem Details, misalnya id kunjungan yang masih aktif.
    """

    status = 400
    tipe = Tipe.PERMINTAAN_TIDAK_VALID
    judul = "Permintaan tidak valid"

    def __init__(
        self,
        detail: str | None = None,
        errors: list[dict[str, str]] | None = None,
        ekstra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(detail or self.judul)
        self.detail = detail
        self.errors = errors
        self.ekstra = ekstra


class TidakDitemukanError(AplikasiError):
    status = 404
    tipe = Tipe.TIDAK_DITEMUKAN
    judul = "Tidak ditemukan"


class KonflikError(AplikasiError):
    status = 409
    tipe = Tipe.KONFLIK
    judul = "Terjadi konflik data"


class ValidasiGagalError(AplikasiError):
    """Validasi yang butuh data dari basis data, sehingga tidak bisa dilakukan oleh model Pydantic."""

    status = 422
    tipe = Tipe.VALIDASI
    judul = "Data tidak valid"

    def __init__(self, errors: list[dict[str, str]], detail: str = "Periksa kembali isian yang ditandai.") -> None:
        super().__init__(detail, errors=errors)


def respons_problem(
    status: int,
    tipe: str,
    judul: str,
    detail: str | None = None,
    errors: list[dict[str, str]] | None = None,
    headers: dict[str, str] | None = None,
    ekstra: dict[str, Any] | None = None,
) -> Response:
    isi: dict[str, Any] = {"type": tipe, "title": judul, "status": status}
    if detail:
        isi["detail"] = detail
    isi["instance"] = request.path
    if errors:
        isi["errors"] = errors
    for kunci, nilai in (ekstra or {}).items():
        isi.setdefault(kunci, nilai)
    respons = Response(json.dumps(isi, ensure_ascii=False), status=status, mimetype=MIMETYPE_PROBLEM)
    for kunci, nilai in (headers or {}).items():
        respons.headers[kunci] = nilai
    return respons


class PenerjemahPesan:
    """Menerjemahkan kode error Pydantic menjadi pesan berbahasa Indonesia per field."""

    # Label field yang tampil di pesan. Field yang belum terdaftar memakai nama field-nya.
    LABEL: ClassVar[dict[str, str]] = {
        "email": "Email",
        "password": "Password",
        "X-Client": "Header X-Client",
        "nama": "Nama",
        "saturasi": "Saturasi oksigen",
        "suhu": "Suhu tubuh",
        "nadi": "Nadi",
        "laju_napas": "Laju napas",
        "td_sistolik": "Tekanan darah sistolik",
        "td_diastolik": "Tekanan darah diastolik",
        "skala_nyeri": "Skala nyeri",
        "keluhan_utama": "Keluhan utama",
        "gejala": "Gejala",
        "kategori_keluhan": "Kategori keluhan",
        "tingkat_kesadaran": "Tingkat kesadaran",
        "tanda_vital": "Tanda vital",
        "id_pemindaian": "ID pemindaian",
        "id_pasien": "ID pasien",
        "tanggal_lahir": "Tanggal lahir",
        "perkiraan_usia": "Perkiraan usia",
        "jenis_kelamin": "Jenis kelamin",
        "nik": "NIK",
        "no_telepon": "Nomor telepon",
        "q": "Kata kunci pencarian",
        "versi_model": "Versi model",
        "ambang_kritis": "Ambang kritis",
        "ambang_tinggi": "Ambang tinggi",
        "ambang_sedang": "Ambang sedang",
        "batas_tunggu_tinggi": "Batas tunggu tinggi",
        "batas_tunggu_sedang": "Batas tunggu sedang",
        "batas_tunggu_rendah": "Batas tunggu rendah",
        "ambang_keyakinan": "Ambang keyakinan",
    }
    SATUAN: ClassVar[dict[str, str]] = {
        "saturasi": "%",
        "suhu": "°C",
        "td_sistolik": " mmHg",
        "td_diastolik": " mmHg",
        "nadi": " x/menit",
        "laju_napas": " x/menit",
        "perkiraan_usia": " tahun",
        "batas_tunggu_tinggi": " menit",
        "batas_tunggu_sedang": " menit",
        "batas_tunggu_rendah": " menit",
    }

    TEMPLAT: ClassVar[dict[str, str]] = {
        "missing": "{label} wajib diisi.",
        "string_too_short": "{label} minimal {min_length} karakter.",
        "string_too_long": "{label} maksimal {max_length} karakter.",
        "string_type": "{label} harus berupa teks.",
        "less_than_equal": "{label} maksimal {le}{satuan}.",
        "greater_than_equal": "{label} minimal {ge}{satuan}.",
        "less_than": "{label} harus kurang dari {lt}{satuan}.",
        "greater_than": "{label} harus lebih dari {gt}{satuan}.",
        "int_parsing": "{label} harus berupa bilangan bulat.",
        "int_type": "{label} harus berupa bilangan bulat.",
        "int_from_float": "{label} harus berupa bilangan bulat.",
        "float_parsing": "{label} harus berupa angka.",
        "float_type": "{label} harus berupa angka.",
        "decimal_parsing": "{label} harus berupa angka.",
        "bool_parsing": "{label} harus bernilai true atau false.",
        "bool_type": "{label} harus bernilai true atau false.",
        "literal_error": "{label} harus salah satu dari: {expected}.",
        "enum": "{label} harus salah satu dari: {expected}.",
        "uuid_parsing": "{label} harus berupa UUID yang valid.",
        "uuid_type": "{label} harus berupa UUID yang valid.",
        "date_parsing": "{label} harus berupa tanggal dengan format YYYY-MM-DD.",
        "date_from_datetime_parsing": "{label} harus berupa tanggal dengan format YYYY-MM-DD.",
        "datetime_parsing": "{label} harus berupa waktu dengan format ISO 8601.",
        "extra_forbidden": "Field {field} tidak dikenal.",
        "list_type": "{label} harus berupa daftar.",
        "dict_type": "{label} harus berupa objek.",
        "too_long": "{label} maksimal berisi {max_length} item.",
        "date_from_datetime_inexact": "{label} harus berupa tanggal dengan format YYYY-MM-DD.",
        "decimal_type": "{label} harus berupa angka.",
        "decimal_max_places": "{label} maksimal {decimal_places} angka di belakang koma.",
        "string_pattern_mismatch": "Format {label} tidak valid.",
        "karakter_tidak_diizinkan": "{label} berisi karakter yang tidak diizinkan.",
    }

    def terjemahkan(self, kode: str, field: str, ctx: dict[str, Any] | None = None, pesan_asli: str = "") -> str:
        ctx = ctx or {}
        # Error buatan validator sendiri (PydanticCustomError berawalan "kustom_") sudah berbahasa Indonesia.
        if kode.startswith(PREFIKS_KODE_KUSTOM):
            return pesan_asli
        templat = self.TEMPLAT.get(kode)
        if kode == "string_too_short" and ctx.get("min_length") == 1:
            templat = self.TEMPLAT["missing"]
        if templat is None:
            return f"{self._label(field)} tidak valid."
        nilai = {
            "label": self._label(field),
            "field": field,
            "satuan": self.SATUAN.get(self._nama_dasar(field), ""),
            **{kunci: self._rapikan(nilai) for kunci, nilai in ctx.items()},
        }
        try:
            return templat.format(**nilai)
        except KeyError:
            return f"{self._label(field)} tidak valid."

    @staticmethod
    def _nama_dasar(field: str) -> str:
        """Nama field terdalam: "tanda_vital.saturasi" menjadi "saturasi", "id_pemindaian.0" menjadi "id_pemindaian"."""
        for bagian in reversed(field.split(".")):
            if not bagian.isdigit():
                return bagian
        return field

    def _label(self, field: str) -> str:
        if field in self.LABEL:
            return self.LABEL[field]
        dasar = self._nama_dasar(field)
        return self.LABEL.get(dasar, field)

    @staticmethod
    def _rapikan(nilai: Any) -> Any:
        # Pydantic menulis pilihan literal sebagai "'web' or 'mobile'".
        if isinstance(nilai, str):
            return nilai.replace("' or '", "', '")
        # Angka ditulis gaya Indonesia: 100.0 menjadi 100, 37.5 menjadi 37,5.
        if isinstance(nilai, float | Decimal) and not isinstance(nilai, bool):
            if nilai == int(nilai):
                return int(nilai)
            return str(nilai).replace(".", ",")
        return nilai


penerjemah = PenerjemahPesan()


def _isi_bukan_objek_json(galat: ValidationError) -> bool:
    """True bila isi request bukan objek JSON (rusak, kosong, atau Content-Type salah)."""
    kode_bukan_objek = ("model_type", "model_attributes_type", "json_invalid", "json_type")
    return any(not e["loc"] and e["type"] in kode_bukan_objek for e in galat.errors())


def respons_validasi_gagal(galat: ValidationError) -> Response:
    """Callback validasi flask-openapi3. Nilai input tidak pernah dikembalikan ke klien."""
    if _isi_bukan_objek_json(galat):
        return respons_problem(
            400,
            Tipe.JSON_TIDAK_VALID,
            "Format JSON tidak valid",
            "Isi permintaan harus berupa objek JSON dengan Content-Type application/json.",
        )
    errors = []
    for e in galat.errors(include_url=False, include_input=False):
        field = ".".join(str(bagian) for bagian in e["loc"]) or "body"
        errors.append({"field": field, "pesan": penerjemah.terjemahkan(e["type"], field, e.get("ctx"), e["msg"])})
    return respons_problem(
        422, Tipe.VALIDASI, "Data tidak valid", "Periksa kembali isian yang ditandai.", errors=errors
    )


JUDUL_HTTP = {
    400: (Tipe.PERMINTAAN_TIDAK_VALID, "Permintaan tidak valid"),
    401: (Tipe.TIDAK_TERAUTENTIKASI, "Belum masuk"),
    403: (Tipe.AKSES_DITOLAK, "Akses ditolak"),
    404: (Tipe.TIDAK_DITEMUKAN, "Tidak ditemukan"),
    405: (Tipe.METODE_TIDAK_DIIZINKAN, "Metode tidak diizinkan"),
    409: (Tipe.KONFLIK, "Terjadi konflik data"),
    413: (Tipe.TERLALU_BESAR, "Isi permintaan terlalu besar"),
}
DETAIL_HTTP = {
    404: "Alamat yang diminta tidak ditemukan.",
    405: "Metode HTTP ini tidak didukung untuk alamat tersebut.",
    413: "Ukuran isi permintaan melebihi batas yang diizinkan.",
}


def _tangani_http(galat: HTTPException) -> Response:
    status = galat.code or 500
    if status >= 500:
        bawaan = (Tipe.KESALAHAN_SERVER, "Terjadi kesalahan pada server")
    else:
        bawaan = (Tipe.PERMINTAAN_TIDAK_VALID, "Permintaan tidak dapat diproses")
    tipe, judul = JUDUL_HTTP.get(status, bawaan)
    # Pertahankan header seperti Allow pada 405.
    headers = {k: v for k, v in galat.get_headers() if k.lower() != "content-type"}
    return respons_problem(status, tipe, judul, DETAIL_HTTP.get(status), headers=headers)


def _tangani_batas_percobaan(_galat: RateLimitExceeded) -> Response:
    # Header Retry-After dan X-RateLimit-* ditambahkan Flask-Limiter setelah respons ini dibuat.
    return respons_problem(
        429,
        Tipe.TERLALU_BANYAK_PERCOBAAN,
        "Terlalu banyak percobaan",
        "Terlalu banyak percobaan masuk yang gagal. Coba lagi beberapa saat lagi.",
    )


def _tangani_galat_aplikasi(galat: AplikasiError) -> Response:
    return respons_problem(galat.status, galat.tipe, galat.judul, galat.detail, galat.errors, ekstra=galat.ekstra)


def _tangani_tak_terduga(galat: Exception) -> Response:
    # Pesan asli bisa memuat host basis data atau isi data pasien, jadi hanya ditulis ke log server.
    logger.exception("Kesalahan tak terduga saat memproses %s %s", request.method, request.path, exc_info=galat)
    return respons_problem(
        500,
        Tipe.KESALAHAN_SERVER,
        "Terjadi kesalahan pada server",
        "Permintaan tidak dapat diproses. Silakan coba lagi atau hubungi admin bila berulang.",
    )


def daftarkan_penangan_error(app: Flask) -> None:
    app.register_error_handler(RateLimitExceeded, _tangani_batas_percobaan)
    app.register_error_handler(AplikasiError, _tangani_galat_aplikasi)
    app.register_error_handler(HTTPException, _tangani_http)
    app.register_error_handler(Exception, _tangani_tak_terduga)
