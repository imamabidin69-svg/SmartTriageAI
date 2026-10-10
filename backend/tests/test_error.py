"""Format Problem Details, penerjemah pesan, dan header keamanan."""

import json
from decimal import Decimal

import pytest
from pydantic import BaseModel, Field, ValidationError

from app import create_app
from app.utils.errors import PenerjemahPesan, Tipe, respons_validasi_gagal


def test_404_berformat_problem_details_dengan_header_keamanan(client):
    respons = client.get("/api/v1/tidak-ada")
    assert respons.status_code == 404
    assert respons.content_type == "application/problem+json"
    assert respons.get_json() == {
        "type": Tipe.TIDAK_DITEMUKAN,
        "title": "Tidak ditemukan",
        "status": 404,
        "detail": "Alamat yang diminta tidak ditemukan.",
        "instance": "/api/v1/tidak-ada",
    }
    assert respons.headers["X-Content-Type-Options"] == "nosniff"
    assert respons.headers["X-Frame-Options"] == "DENY"
    assert respons.headers["Referrer-Policy"] == "no-referrer"
    assert respons.headers["Content-Security-Policy"] == "default-src 'none'; frame-ancestors 'none'"
    assert respons.headers["Cache-Control"] == "no-store"
    assert "Strict-Transport-Security" not in respons.headers


def test_header_api_tidak_dipasang_di_luar_prefiks_api(client):
    respons = client.get("/halaman-lain")
    assert respons.headers["X-Frame-Options"] == "DENY"
    assert "Cache-Control" not in respons.headers


def test_405_mempertahankan_header_allow(client):
    respons = client.get("/api/v1/auth/login")
    assert respons.status_code == 405
    assert respons.get_json()["type"] == Tipe.METODE_TIDAK_DIIZINKAN
    assert "POST" in respons.headers["Allow"]


def test_413_isi_terlalu_besar(client):
    isi = json.dumps({"email": "a@smarttriage.demo", "password": "x" * (1024 * 1024)})
    respons = client.post("/api/v1/auth/login", data=isi, content_type="application/json")
    assert respons.status_code == 413
    assert respons.get_json()["type"] == Tipe.TERLALU_BESAR


def test_json_bersarang_terlalu_dalam_dibalas_400(client, caplog):
    respons = client.post("/api/v1/auth/login", data="[" * 200_000, content_type="application/json")
    assert respons.status_code == 400
    assert respons.get_json()["type"] == Tipe.JSON_TIDAK_VALID
    assert "Kesalahan tak terduga" not in caplog.text


def test_hsts_hanya_di_production(konfigurasi_app):
    aplikasi = create_app({**konfigurasi_app, "APP_ENV": "production"})
    respons = aplikasi.test_client().get("/api/v1/health")
    assert respons.headers["Strict-Transport-Security"] == "max-age=31536000"


def test_dokumentasi_api_hanya_di_development(app, konfigurasi_app):
    assert app.test_client().get("/api/v1/openapi/openapi.json").status_code == 404

    aplikasi = create_app({**konfigurasi_app, "APP_ENV": "development"})
    respons = aplikasi.test_client().get("/api/v1/openapi/openapi.json")
    assert respons.status_code == 200
    # CSP ketat API tidak dipasang di halaman dokumentasi supaya Swagger UI tetap bisa dimuat.
    assert "Content-Security-Policy" not in respons.headers
    spesifikasi = respons.get_json()
    assert spesifikasi["openapi"].startswith("3.1")
    login = spesifikasi["paths"]["/api/v1/auth/login"]["post"]
    assert "application/problem+json" in login["responses"]["422"]["content"]
    assert any(p["name"] == "X-Client" and p["in"] == "header" for p in login["parameters"])
    assert set(spesifikasi["components"]["securitySchemes"]) == {"bearerAuth", "cookieAccess", "cookieRefresh"}
    assert spesifikasi["paths"]["/api/v1/auth/me"]["get"]["security"] == [{"bearerAuth": []}, {"cookieAccess": []}]
    # Error didokumentasikan dengan Content-Type yang sebenarnya dikirim server.
    for kode in ("400", "401", "403", "429"):
        assert list(login["responses"][kode]["content"]) == ["application/problem+json"]
    health = spesifikasi["paths"]["/api/v1/health"]["get"]["responses"]
    assert "content" not in health.get("422", {})


class _Contoh(BaseModel):
    saturasi: float = Field(le=100)
    nama: str = Field(min_length=2, max_length=5)


def test_respons_validasi_untuk_field_bertingkat(app):
    class Induk(BaseModel):
        tanda_vital: _Contoh

    with pytest.raises(ValidationError) as galat:
        Induk.model_validate({"tanda_vital": {"saturasi": 120, "nama": "a"}})
    with app.test_request_context("/api/v1/x"):
        respons = respons_validasi_gagal(galat.value)
    assert respons.status_code == 422
    assert respons.get_json()["errors"] == [
        {"field": "tanda_vital.saturasi", "pesan": "tanda_vital.saturasi maksimal 100."},
        {"field": "tanda_vital.nama", "pesan": "tanda_vital.nama minimal 2 karakter."},
    ]


@pytest.mark.parametrize(
    ("kode", "field", "ctx", "pesan"),
    [
        ("less_than_equal", "saturasi", {"le": 100}, "Saturasi oksigen maksimal 100%."),
        ("greater_than_equal", "suhu", {"ge": 20}, "Suhu tubuh minimal 20°C."),
        ("greater_than_equal", "suhu", {"ge": 35.5}, "Suhu tubuh minimal 35,5°C."),
        ("less_than_equal", "saturasi", {"le": Decimal("100.0")}, "Saturasi oksigen maksimal 100%."),
        ("less_than", "nadi", {"lt": 300}, "Nadi harus kurang dari 300."),
        ("greater_than", "nadi", {"gt": 0}, "Nadi harus lebih dari 0."),
        ("string_too_long", "nama", {"max_length": 120}, "Nama maksimal 120 karakter."),
        ("string_too_short", "nama", {"min_length": 1}, "Nama wajib diisi."),
        ("int_parsing", "nadi", None, "Nadi harus berupa bilangan bulat."),
        ("float_parsing", "suhu", None, "Suhu tubuh harus berupa angka."),
        ("bool_parsing", "aktif", None, "aktif harus bernilai true atau false."),
        (
            "literal_error",
            "peran",
            {"expected": "'perawat' or 'dokter'"},
            "peran harus salah satu dari: 'perawat', 'dokter'.",
        ),
        (
            "enum",
            "peran",
            {"expected": "'perawat', 'dokter' or 'admin'"},
            "peran harus salah satu dari: 'perawat', 'dokter', 'admin'.",
        ),
        ("uuid_parsing", "id", None, "id harus berupa UUID yang valid."),
        ("date_parsing", "tanggal_lahir", None, "tanggal_lahir harus berupa tanggal dengan format YYYY-MM-DD."),
        ("extra_forbidden", "role", None, "Field role tidak dikenal."),
        ("kode_baru_pydantic", "nama", None, "Nama tidak valid."),
        # Templat butuh nilai ctx yang tidak ada: jatuh ke pesan umum, bukan error.
        ("less_than_equal", "nadi", None, "Nadi tidak valid."),
    ],
)
def test_penerjemah_pesan(kode, field, ctx, pesan):
    assert PenerjemahPesan().terjemahkan(kode, field, ctx) == pesan


def test_pesan_kustom_dipakai_apa_adanya():
    assert PenerjemahPesan().terjemahkan("kustom_email", "email", None, "Format email tidak valid.") == (
        "Format email tidak valid."
    )
