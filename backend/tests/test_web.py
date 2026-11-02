"""SpaRoute: Flask menyajikan hasil build aplikasi web React (Desain baris 101 dan 432, keputusan W3)."""

import pytest

from app import create_app
from app.routes.spa import CACHE_ASET, CACHE_HALAMAN, CSP_WEB


@pytest.fixture(scope="module")
def folder_web(tmp_path_factory):
    folder = tmp_path_factory.mktemp("dist")
    (folder / "index.html").write_text("<!doctype html><title>SmartTriage AI</title>", encoding="utf-8")
    (folder / "assets").mkdir()
    (folder / "assets" / "index-abc123.js").write_text("console.log('web')", encoding="utf-8")
    (folder / "sw.js").write_text("self.addEventListener('install', () => {})", encoding="utf-8")
    (folder.parent / "rahasia.txt").write_text("jangan disajikan", encoding="utf-8")
    return folder


class _KlienTertutup:
    """Respons berkas dari send_from_directory dibaca lalu ditutup, supaya berkasnya tidak dibiarkan terbuka."""

    def __init__(self, klien):
        self.klien = klien

    def open(self, *args, **kwargs):
        respons = self.klien.open(*args, **kwargs)
        respons.get_data()
        respons.close()
        return respons

    def get(self, alamat):
        return self.open(alamat, method="GET")

    def post(self, alamat):
        return self.open(alamat, method="POST")


@pytest.fixture(scope="module")
def klien_web(konfigurasi_app, app, folder_web):
    return _KlienTertutup(create_app({**konfigurasi_app, "WEB_DIST_PATH": str(folder_web)}).test_client())


@pytest.mark.parametrize("alamat", ["/", "/staf", "/log-audit", "/eir"])
def test_rute_klien_dijawab_index_html(klien_web, alamat):
    respons = klien_web.get(alamat)
    assert respons.status_code == 200
    assert "SmartTriage AI" in respons.get_data(as_text=True)
    assert respons.headers["Cache-Control"] == CACHE_HALAMAN
    assert respons.headers["Content-Security-Policy"] == CSP_WEB


def test_aset_ber_hash_disimpan_lama(klien_web):
    respons = klien_web.get("/assets/index-abc123.js")
    assert respons.status_code == 200
    assert respons.headers["Cache-Control"] == CACHE_ASET


def test_service_worker_selalu_dicek_ulang(klien_web):
    respons = klien_web.get("/sw.js")
    assert respons.status_code == 200
    assert respons.headers["Cache-Control"] == CACHE_HALAMAN


@pytest.mark.parametrize("alamat", ["/assets/index-lama.js", "/favicon.ico"])
def test_berkas_yang_tidak_ada_404(klien_web, alamat):
    respons = klien_web.get(alamat)
    assert respons.status_code == 404
    assert respons.content_type == "application/problem+json"


def test_berkas_di_luar_folder_tidak_disajikan(klien_web):
    respons = klien_web.get("/..%2frahasia.txt")
    assert "jangan disajikan" not in respons.get_data(as_text=True)


@pytest.mark.parametrize(("metode", "alamat", "kode"), [("GET", "/api/v1/tidak-ada", 404), ("GET", "/api", 404)])
def test_alamat_api_tidak_dijawab_halaman_react(klien_web, metode, alamat, kode):
    respons = klien_web.open(alamat, method=metode)
    assert respons.status_code == kode
    assert respons.content_type == "application/problem+json"


def test_halaman_web_hanya_get(klien_web):
    assert klien_web.post("/staf").status_code == 405


def test_web_belum_dibangun(konfigurasi_app, app, tmp_path):
    klien = create_app({**konfigurasi_app, "WEB_DIST_PATH": str(tmp_path / "kosong")}).test_client()
    respons = klien.get("/staf")
    assert respons.status_code == 404
    assert respons.get_json()["title"] == "Aplikasi web belum dibangun"


def test_lokasi_web_dari_environment(monkeypatch):
    from app.config import DIREKTORI_BACKEND, buat_konfigurasi

    assert buat_konfigurasi("testing")["WEB_DIST_PATH"] == str(DIREKTORI_BACKEND.parent / "web" / "dist")
    monkeypatch.setenv("WEB_DIST_PATH", "static")
    assert buat_konfigurasi("testing")["WEB_DIST_PATH"] == str(DIREKTORI_BACKEND / "static")
