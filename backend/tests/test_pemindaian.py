"""POST /pemindaian (FR-04, Desain 2.4 dan Gambar 2.10-2.12, keputusan P1-P8)."""

import io
from datetime import timedelta
from decimal import Decimal

import pytest
from bantuan import header_masuk
from PIL import Image
from sqlalchemy import select, update
from werkzeug.datastructures import FileStorage
from werkzeug.test import encode_multipart

from app import create_app
from app.ai.pembaca_layar import Digit, PembacaLayarTiruan, digit_dari_baris
from app.models import Konfigurasi, PemindaianAlat
from app.models.enums import JenisAlat, Peran
from app.services import pemindaian_service
from app.services.rekap_service import RekapService
from app.utils.errors import Tipe
from app.utils.request import RequestTanpaBerkasSementara
from app.utils.waktu import hari_ini

URL = "/api/v1/pemindaian"


def _foto(format_: str = "JPEG", ukuran: tuple[int, int] = (800, 600)) -> bytes:
    keluaran = io.BytesIO()
    Image.new("RGB", ukuran, (30, 30, 30)).save(keluaran, format=format_)
    return keluaran.getvalue()


def _post_multipart(client, header, isi: dict):
    # Body multipart disusun di memori. Test client Werkzeug menampung body besar di berkas sementara
    # yang tidak ditutup bila request ditolak sebelum dibaca, sehingga memicu ResourceWarning.
    batas, body = encode_multipart(isi)
    return client.post(URL, data=body, headers=header, content_type=f"multipart/form-data; boundary={batas}")


def _kirim(client, header, jenis="tensimeter", data: bytes | None = None, nama="layar.jpg", **lain):
    isi = {"jenis_alat": jenis, **lain}
    if data is not None or "berkas" not in lain:
        isi["berkas"] = FileStorage(io.BytesIO(_foto() if data is None else data), filename=nama)
    return _post_multipart(client, header, isi)


@pytest.fixture
def perawat(masuk):
    return masuk(Peran.PERAWAT)


@pytest.fixture
def pakai_digit(app, monkeypatch):
    """Mengganti digit yang dikembalikan pembaca tiruan untuk satu tes."""

    def _pakai(jenis: JenisAlat, baris: list[str], keyakinan: float = 0.97):
        pembaca = PembacaLayarTiruan({jenis: digit_dari_baris(baris, keyakinan)})
        monkeypatch.setattr(app.extensions["model_registry"], "pembaca_layar", pembaca)

    return _pakai


# ---------------------------------------------------------------- hasil baca


def test_tensimeter_terbaca_dan_tersimpan_tanpa_foto(client, perawat, sesi_db):
    pengguna, header = perawat
    respons = _kirim(client, header)

    assert respons.status_code == 200
    isi = respons.get_json()
    assert isi["jenis_alat"] == "tensimeter"
    assert isi["nilai"] == {"td_sistolik": 128, "td_diastolik": 84, "nadi": 76}
    # Nilai bulat tetap bilangan bulat di JSON, bukan 128.0.
    assert '"td_sistolik":128' in respons.get_data(as_text=True).replace(" ", "")
    assert isi["keyakinan"] == {"td_sistolik": 0.97, "td_diastolik": 0.97, "nadi": 0.97}
    assert isi["kolom_kosong"] == []
    assert isi["pembaca_tersedia"] is True

    baris = sesi_db.get(PemindaianAlat, isi["id_pemindaian"])
    assert baris.dipindai_oleh == pengguna.id_pengguna
    assert baris.jenis_alat == JenisAlat.TENSIMETER
    assert baris.nilai_terbaca == {"td_sistolik": 128, "td_diastolik": 84, "nadi": 76}
    assert baris.nilai_dikonfirmasi is None
    assert baris.id_triase is None
    assert baris.keyakinan == Decimal("0.970")
    # Tabel ini memang tidak punya kolom untuk foto.
    assert not {"foto", "gambar", "berkas"} & set(PemindaianAlat.__table__.columns.keys())


@pytest.mark.parametrize(
    ("jenis", "nilai"),
    [
        ("oksimeter", {"saturasi": 97, "nadi": 82}),
        ("termometer", {"suhu": 36.8}),
    ],
)
def test_alat_lain(client, perawat, jenis, nilai):
    _, header = perawat
    isi = _kirim(client, header, jenis).get_json()
    assert isi["nilai"] == nilai
    assert isi["kolom_kosong"] == []


def test_bedside_monitor_dikosongkan(client, perawat, sesi_db):
    _, header = perawat
    isi = _kirim(client, header, "bedside_monitor").get_json()
    kolom = ["td_sistolik", "td_diastolik", "nadi", "laju_napas", "suhu", "saturasi"]
    assert isi["nilai"] == dict.fromkeys(kolom)
    assert isi["kolom_kosong"] == kolom
    assert sesi_db.get(PemindaianAlat, isi["id_pemindaian"]).nilai_terbaca == {}


def test_png_juga_diterima(client, perawat):
    _, header = perawat
    assert _kirim(client, header, data=_foto("PNG"), nama="layar.png").status_code == 200


def test_keyakinan_di_bawah_ambang_dikosongkan(client, perawat, pakai_digit, sesi_db):
    pakai_digit(JenisAlat.OKSIMETER, ["97", "82"], keyakinan=0.6)
    _, header = perawat
    isi = _kirim(client, header, "oksimeter").get_json()
    assert isi["nilai"] == {"saturasi": None, "nadi": None}
    # Keyakinan tetap dikirim supaya perawat tahu kolom itu terbaca tetapi ragu.
    assert isi["keyakinan"] == {"saturasi": 0.6, "nadi": 0.6}
    assert isi["kolom_kosong"] == ["saturasi", "nadi"]
    baris = sesi_db.get(PemindaianAlat, isi["id_pemindaian"])
    # Keputusan P1: tidak ada kolom terisi, jadi keyakinan baris = keyakinan digit tertinggi.
    assert (baris.nilai_terbaca, baris.keyakinan) == ({}, Decimal("0.600"))


def test_ambang_mengikuti_konfigurasi(client, perawat, pakai_digit, sesi_db):
    sesi_db.execute(update(Konfigurasi).values(ambang_keyakinan=Decimal("0.50")))
    sesi_db.commit()
    pakai_digit(JenisAlat.OKSIMETER, ["97", "82"], keyakinan=0.6)
    _, header = perawat
    assert _kirim(client, header, "oksimeter").get_json()["nilai"] == {"saturasi": 97, "nadi": 82}


def test_nilai_di_luar_rentang_wajar_dikosongkan(client, perawat, pakai_digit):
    # Nadi 300 di atas batas salah ketik 250; sistolik 128 dan diastolik 84 tetap terisi.
    pakai_digit(JenisAlat.TENSIMETER, ["128", "84", "300"])
    _, header = perawat
    isi = _kirim(client, header).get_json()
    assert isi["nilai"] == {"td_sistolik": 128, "td_diastolik": 84, "nadi": None}
    assert isi["kolom_kosong"] == ["nadi"]


def test_nilai_abnormal_tetap_terbaca(client, perawat, pakai_digit):
    # Keputusan P3: saturasi 85% tidak wajar secara klinis tetapi mungkin benar, jadi tetap diisi.
    pakai_digit(JenisAlat.OKSIMETER, ["85", "128"])
    _, header = perawat
    assert _kirim(client, header, "oksimeter").get_json()["nilai"] == {"saturasi": 85, "nadi": 128}


def test_keyakinan_baris_adalah_kolom_terisi_terendah(client, perawat, app, monkeypatch, sesi_db):
    digit = digit_dari_baris(["97", "82"])
    digit[0] = Digit(9, 0.88, digit[0].x1, digit[0].y1, digit[0].x2, digit[0].y2)
    monkeypatch.setattr(
        app.extensions["model_registry"], "pembaca_layar", PembacaLayarTiruan({JenisAlat.OKSIMETER: digit})
    )
    _, header = perawat
    isi = _kirim(client, header, "oksimeter").get_json()
    assert sesi_db.get(PemindaianAlat, isi["id_pemindaian"]).keyakinan == Decimal("0.880")


def test_tanpa_digit_keyakinan_nol(client, perawat, pakai_digit, sesi_db):
    pakai_digit(JenisAlat.TERMOMETER, [])
    _, header = perawat
    isi = _kirim(client, header, "termometer").get_json()
    assert isi["nilai"] == {"suhu": None}
    assert isi["keyakinan"] == {"suhu": None}
    assert sesi_db.get(PemindaianAlat, isi["id_pemindaian"]).keyakinan == Decimal("0.000")


# ---------------------------------------------------------------- tanpa model dan pembaca gagal


def test_tanpa_model_yolo_semua_kolom_kosong(konfigurasi_app, buat_pengguna, sesi_db):
    tanpa_yolo = create_app({**konfigurasi_app, "PEMBACA_LAYAR": "onnx", "MODEL_YOLO_PATH": "/tidak/ada/yolo.onnx"})
    klien = tanpa_yolo.test_client()
    header = header_masuk(klien, buat_pengguna(Peran.PERAWAT).email)
    respons = _kirim(klien, header)

    assert respons.status_code == 200
    isi = respons.get_json()
    assert isi["pembaca_tersedia"] is False
    assert isi["nilai"] == {"td_sistolik": None, "td_diastolik": None, "nadi": None}
    assert sesi_db.get(PemindaianAlat, isi["id_pemindaian"]).nilai_terbaca == {}


def test_pembaca_error_tidak_menggagalkan_pemindaian(client, perawat, app, monkeypatch, caplog):
    class PembacaRusak(PembacaLayarTiruan):
        def deteksi(self, gambar, jenis_alat):
            raise RuntimeError("sesi onnx rusak")

    monkeypatch.setattr(app.extensions["model_registry"], "pembaca_layar", PembacaRusak())
    _, header = perawat
    respons = _kirim(client, header)
    assert respons.status_code == 200
    assert respons.get_json()["kolom_kosong"] == ["td_sistolik", "td_diastolik", "nadi"]
    assert "Pembaca layar gagal" in caplog.text


# ---------------------------------------------------------------- validasi berkas


@pytest.mark.parametrize(
    ("data", "nama", "pesan"),
    [
        (b"ini bukan gambar", "layar.jpg", "Berkas bukan foto JPEG atau PNG yang valid."),
        (b"", "layar.jpg", "Foto kosong."),
        ("GIF", "layar.gif", "Foto harus berformat JPEG atau PNG."),
        ("terpotong", "layar.jpg", "Berkas bukan foto JPEG atau PNG yang valid."),
    ],
)
def test_berkas_tidak_valid(client, perawat, sesi_db, data, nama, pesan):
    if data == "GIF":
        data = _foto("GIF")
    elif data == "terpotong":
        data = _foto()[:400]
    _, header = perawat
    respons = _kirim(client, header, data=data, nama=nama)
    assert respons.status_code == 422
    assert respons.get_json()["errors"] == [{"field": "berkas", "pesan": pesan}]
    assert sesi_db.scalars(select(PemindaianAlat)).all() == []


def test_foto_lebih_dari_batas_ukuran(client, perawat, app, monkeypatch):
    monkeypatch.setitem(app.config, "UKURAN_MAKS_FOTO", 2 * 1024 * 1024)
    _, header = perawat
    besar = _foto(ukuran=(2000, 2000)) + b"\0" * (2 * 1024 * 1024)
    respons = _kirim(client, header, data=besar)
    assert respons.status_code == 422
    assert respons.get_json()["errors"] == [{"field": "berkas", "pesan": "Ukuran foto maksimal 2 MB."}]


def test_request_terlalu_besar_dibalas_413(client, perawat, app, monkeypatch):
    monkeypatch.setitem(app.config, "UKURAN_MAKS_REQUEST_FOTO", 100 * 1024)
    _, header = perawat
    respons = _kirim(client, header, data=b"\xff" * (200 * 1024))
    assert respons.status_code == 413
    assert respons.get_json()["type"] == Tipe.TERLALU_BESAR


def test_foto_di_atas_1_mib_tetap_diterima(client, perawat):
    # Batas umum request 1 MiB dinaikkan khusus untuk endpoint ini.
    _, header = perawat
    data = _foto("PNG") + b"\0" * (2 * 1024 * 1024)
    assert _kirim(client, header, data=data, nama="layar.png").status_code == 200


def test_resolusi_terlalu_besar_ditolak(client, perawat, monkeypatch):
    monkeypatch.setattr(pemindaian_service, "PIKSEL_MAKSIMUM", 1000)
    _, header = perawat
    respons = _kirim(client, header)
    assert respons.get_json()["errors"] == [{"field": "berkas", "pesan": "Resolusi foto terlalu besar."}]


@pytest.mark.parametrize(
    ("isi", "field", "pesan"),
    [
        ({"jenis_alat": "timbangan"}, "jenis_alat", None),
        ({"berkas": "teks biasa"}, "berkas", "Foto harus dikirim sebagai berkas."),
    ],
)
def test_isian_form_tidak_valid(client, perawat, isi, field, pesan):
    _, header = perawat
    data = {"jenis_alat": "tensimeter", "berkas": FileStorage(io.BytesIO(_foto()), filename="layar.jpg"), **isi}
    respons = _post_multipart(client, header, data)
    assert respons.status_code == 422
    [galat] = respons.get_json()["errors"]
    assert galat["field"] == field
    if pesan:
        assert galat["pesan"] == pesan


def test_berkas_wajib(client, perawat):
    _, header = perawat
    respons = _post_multipart(client, header, {"jenis_alat": "tensimeter"})
    assert respons.status_code == 422
    assert respons.get_json()["errors"] == [{"field": "berkas", "pesan": "Foto wajib diisi."}]


def test_unggahan_ditampung_di_memori_bukan_disk():
    request = RequestTanpaBerkasSementara.from_values()
    aliran = request._get_file_stream(10 * 1024 * 1024, "image/jpeg", "layar.jpg")
    assert isinstance(aliran, io.BytesIO)


# ---------------------------------------------------------------- peran


@pytest.mark.parametrize("peran", [Peran.DOKTER, Peran.ADMIN])
def test_hanya_perawat_yang_memindai(client, masuk, peran):
    _, header = masuk(peran)
    assert _kirim(client, header).status_code == 403


def test_tanpa_login(client):
    assert _kirim(client, {}).status_code == 401


# ---------------------------------------------------------------- alur sampai triase dan rekap


ISIAN_TRIASE = {
    "keluhan_utama": "Pusing",
    "gejala": "Pusing berputar sejak pagi tanpa muntah",
    "kategori_keluhan": "Pusing",
    "skala_nyeri": 2,
    "tingkat_kesadaran": "A",
}


def test_hasil_pemindaian_dipakai_form_triase_dan_masuk_rekap(client, perawat, kunjungan, sesi_db):
    _, header = perawat
    tensi = _kirim(client, header).get_json()["id_pemindaian"]
    oksi = _kirim(client, header, "oksimeter").get_json()["id_pemindaian"]

    # Perawat memakai nadi dari tensimeter (76), jadi nadi oksimeter (82) terhitung salah baca.
    tanda_vital = {
        "td_sistolik": 128,
        "td_diastolik": 84,
        "nadi": 76,
        "laju_napas": 18,
        "suhu": 36.8,
        "saturasi": 97,
    }
    respons = client.post(
        f"/api/v1/kunjungan/{kunjungan.id_kunjungan}/triase",
        json={**ISIAN_TRIASE, "tanda_vital": tanda_vital, "id_pemindaian": [tensi, oksi]},
        headers=header,
    )
    assert respons.status_code == 201
    assert respons.get_json()["sumber_tanda_vital"] == "campuran"
    baris_tensi = sesi_db.get(PemindaianAlat, tensi)
    sesi_db.refresh(baris_tensi)
    assert baris_tensi.nilai_dikonfirmasi == {"nadi": 76, "td_diastolik": 84, "td_sistolik": 128}

    # Lima kolom terbaca (3 tensimeter + 2 oksimeter), satu tidak cocok: 4/5 = 80%.
    assert RekapService().akurasi_pemindaian(hari_ini(), hari_ini()) == 80.0
    assert RekapService().akurasi_pemindaian(hari_ini() - timedelta(days=9), hari_ini() - timedelta(days=8)) is None


def test_pemindaian_yang_belum_dipakai_tidak_dihitung(client, perawat):
    _, header = perawat
    _kirim(client, header)
    assert RekapService().akurasi_pemindaian(hari_ini(), hari_ini()) is None
