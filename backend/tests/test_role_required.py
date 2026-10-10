"""RBAC tiga peran dengan @role_required dan aturan default-deny (NFR-01)."""

import re

import pytest
import sqlalchemy as sa
from bantuan import bearer, login_mobile, login_web, nilai_cookie
from flask import abort, jsonify
from flask_openapi3 import APIBlueprint, validate_request
from pydantic import BaseModel, Field

from app import create_app
from app.middleware.auth import role_required
from app.models import Pengguna
from app.models.enums import Peran
from app.utils.errors import Tipe

ENDPOINT_PUBLIK = {"api_v1.auth.login", "api_v1.health.health"}


class CatatanUji(BaseModel):
    catatan: str = Field(min_length=5)


@pytest.fixture(scope="module")
def app_uji(konfigurasi_app):
    """Aplikasi terpisah dengan rute khusus tes, karena rute tidak bisa ditambah setelah app dipakai."""
    aplikasi = create_app(konfigurasi_app)
    bp = APIBlueprint("uji", __name__, url_prefix="/api/v1/uji")

    @bp.get("/admin")
    @role_required(Peran.ADMIN)
    def khusus_admin():
        return jsonify(ok=True)

    @bp.post("/klinis")
    @role_required(Peran.PERAWAT, Peran.DOKTER)
    @validate_request()
    def khusus_klinis(body: CatatanUji):
        return jsonify(catatan=body.catatan)

    @bp.get("/galat")
    def galat_tak_terduga():
        raise RuntimeError('connection to server at "db.internal" password=rahasia')

    @bp.get("/teko")
    def teko():
        abort(418)

    @bp.get("/tidak-tersedia")
    def tidak_tersedia():
        abort(503)

    aplikasi.register_api(bp)
    return aplikasi


def test_tanpa_token_dibalas_401(app_uji):
    respons = app_uji.test_client().get("/api/v1/uji/admin")
    assert respons.status_code == 401


@pytest.mark.parametrize(
    ("peran", "metode", "path", "status"),
    [
        (Peran.ADMIN, "GET", "/api/v1/uji/admin", 200),
        (Peran.PERAWAT, "GET", "/api/v1/uji/admin", 403),
        (Peran.DOKTER, "GET", "/api/v1/uji/admin", 403),
        # Admin tidak boleh mengakses fitur klinis (SKPL Tabel 2.1).
        (Peran.ADMIN, "POST", "/api/v1/uji/klinis", 403),
        (Peran.PERAWAT, "POST", "/api/v1/uji/klinis", 200),
        (Peran.DOKTER, "POST", "/api/v1/uji/klinis", 200),
    ],
)
def test_matriks_peran(app_uji, buat_pengguna, peran, metode, path, status):
    klien = app_uji.test_client()
    token = login_mobile(klien, buat_pengguna(peran).email).get_json()["access_token"]
    respons = klien.open(path, method=metode, json={"catatan": "pasien gelisah"}, headers=bearer(token))
    assert respons.status_code == status
    if status == 403:
        assert respons.get_json()["type"] == Tipe.AKSES_DITOLAK


def test_perubahan_akun_berlaku_di_tengah_sesi(app_uji, buat_pengguna, sesi_db):
    """Desain 2.1: pengguna dibaca ulang setiap request, jadi perubahan admin langsung berlaku."""
    klien = app_uji.test_client()
    pengguna = buat_pengguna(Peran.ADMIN)
    token = login_mobile(klien, pengguna.email).get_json()["access_token"]
    assert klien.get("/api/v1/uji/admin", headers=bearer(token)).status_code == 200

    ubah = sa.update(Pengguna).where(Pengguna.id_pengguna == pengguna.id_pengguna)
    sesi_db.execute(ubah.values(peran=Peran.PERAWAT))
    sesi_db.commit()
    assert klien.get("/api/v1/uji/admin", headers=bearer(token)).status_code == 403

    sesi_db.execute(ubah.values(is_active=False))
    sesi_db.commit()
    respons = klien.get("/api/v1/uji/admin", headers=bearer(token))
    assert respons.status_code == 401
    assert respons.get_json()["type"] == Tipe.SESI_BERAKHIR


def test_peran_dibaca_dari_basis_data_bukan_dari_token(app_uji, buat_pengguna, sesi_db):
    klien = app_uji.test_client()
    pengguna = buat_pengguna(Peran.ADMIN)
    token = login_mobile(klien, pengguna.email).get_json()["access_token"]
    # Diubah lewat UPDATE karena objek pengguna sudah terlepas dari sesi setelah request app_uji selesai.
    sesi_db.execute(sa.update(Pengguna).where(Pengguna.id_pengguna == pengguna.id_pengguna).values(peran=Peran.PERAWAT))
    sesi_db.commit()
    assert klien.get("/api/v1/uji/admin", headers=bearer(token)).status_code == 403


def test_autentikasi_diperiksa_sebelum_validasi_isi(app_uji, buat_pengguna):
    klien = app_uji.test_client()
    # Tanpa token, isi yang salah tetap dibalas 401, bukan 422.
    assert klien.post("/api/v1/uji/klinis", json={"catatan": "x"}).status_code == 401

    token = login_mobile(klien, buat_pengguna(Peran.DOKTER).email).get_json()["access_token"]
    respons = klien.post("/api/v1/uji/klinis", json={"catatan": "x"}, headers=bearer(token))
    assert respons.status_code == 422
    assert respons.get_json()["errors"] == [{"field": "catatan", "pesan": "catatan minimal 5 karakter."}]


def test_post_lewat_cookie_wajib_token_csrf(app_uji, buat_pengguna):
    klien = app_uji.test_client()
    login_web(klien, buat_pengguna(Peran.PERAWAT).email)
    assert klien.post("/api/v1/uji/klinis", json={"catatan": "pasien gelisah"}).status_code == 401

    respons = klien.post(
        "/api/v1/uji/klinis",
        json={"catatan": "pasien gelisah"},
        headers={"X-CSRF-TOKEN": nilai_cookie(klien, "csrf_access_token")},
    )
    assert respons.status_code == 200


def test_role_required_tanpa_peran_ditolak():
    with pytest.raises(ValueError, match="minimal satu peran"):
        role_required()


def test_semua_endpoint_api_selain_publik_menolak_tanpa_token(app):
    """Default-deny: endpoint baru yang lupa diberi dekorator autentikasi akan gagal di tes ini."""
    klien = app.test_client()
    diperiksa = 0
    for aturan in app.url_map.iter_rules():
        if not aturan.rule.startswith("/api/v1/") or aturan.endpoint in ENDPOINT_PUBLIK:
            continue
        if aturan.rule.startswith(app.config["PREFIKS_DOKUMENTASI"]):
            continue
        # Nilai contoh sesuai konverter rute, misalnya <uuid:id> atau <int:id>.
        path = re.sub(
            r"<(?:(\w+)(?:\([^>]*\))?:)?\w+>",
            lambda m: {"int": "1", "float": "1.0"}.get(m.group(1), "00000000-0000-0000-0000-000000000000"),
            aturan.rule,
        )
        for metode in aturan.methods - {"HEAD", "OPTIONS"}:
            respons = klien.open(path, method=metode, json={})
            assert respons.status_code != 404, f"path uji {path} tidak cocok dengan {aturan.rule}"
            assert respons.status_code == 401, f"{metode} {aturan.rule} tidak dilindungi"
            diperiksa += 1
    assert diperiksa >= 3


def test_kesalahan_tak_terduga_tidak_membocorkan_detail(app_uji, caplog):
    respons = app_uji.test_client().get("/api/v1/uji/galat")
    assert respons.status_code == 500
    assert respons.content_type == "application/problem+json"
    teks = respons.get_data(as_text=True)
    assert "rahasia" not in teks
    assert "db.internal" not in teks
    assert respons.get_json()["type"] == Tipe.KESALAHAN_SERVER
    assert "Kesalahan tak terduga" in caplog.text


def test_status_http_lain_tetap_problem_details_berbahasa_indonesia(app_uji):
    respons = app_uji.test_client().get("/api/v1/uji/teko")
    assert respons.status_code == 418
    assert respons.get_json()["title"] == "Permintaan tidak dapat diproses"
    assert respons.get_json()["type"] == Tipe.PERMINTAAN_TIDAK_VALID

    respons = app_uji.test_client().get("/api/v1/uji/tidak-tersedia")
    assert respons.status_code == 503
    assert respons.get_json()["title"] == "Terjadi kesalahan pada server"
    assert respons.get_json()["type"] == Tipe.KESALAHAN_SERVER
