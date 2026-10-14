"""GET /daftar-tunggu dan penanda triase ulang (FR-07, Desain 2.7, Gambar 2.19, keputusan K1a dan K11)."""

from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import update

from app.models import Konfigurasi
from app.models.enums import Peran, RiskLevel, StatusKunjungan, StatusValidasi
from app.services.daftar_tunggu_service import DaftarTungguService
from app.services.konfigurasi_service import cache_konfigurasi
from app.utils.waktu import sekarang

URL = "/api/v1/daftar-tunggu"


@pytest.fixture
def perawat(masuk):
    return masuk(Peran.PERAWAT)


def _menit_lalu(acuan: datetime, menit: float) -> datetime:
    return acuan - timedelta(minutes=menit)


def _susun(app, waktu):
    with app.app_context():
        return DaftarTungguService(cache_konfigurasi().ambil()).susun(waktu)


def test_isi_item_daftar_tunggu(client, perawat, buat_kunjungan, buat_triase):
    waktu = sekarang()
    kunjungan = buat_kunjungan("Agus", _menit_lalu(waktu, 40), tanggal_lahir=date(1990, 1, 1), perkiraan_usia=None)
    triase = buat_triase(kunjungan, RiskLevel.SEDANG, waktu=_menit_lalu(waktu, 12))
    _, header = perawat
    respons = client.get(URL, headers=header)

    assert respons.status_code == 200
    isi = respons.get_json()
    assert datetime.fromisoformat(isi["waktu_server"]).tzinfo is not None
    [item] = isi["items"]
    assert item["id_kunjungan"] == str(kunjungan.id_kunjungan)
    assert item["pasien"]["nama"] == "Agus"
    # Usia dari tanggal lahir 1 Januari, jadi selalu sudah berulang tahun pada tahun berjalan.
    assert item["pasien"]["usia"] == waktu.year - 1990
    assert datetime.fromisoformat(item["triase_terakhir"].pop("waktu_triase")) == triase.waktu_triase
    assert item["triase_terakhir"] == {
        "id_triase": str(triase.id_triase),
        "jenis": "awal",
        "risk_level": "sedang",
        "status_validasi": "menunggu",
        "keluhan_utama": "Pusing",
    }
    # Lama menunggu dihitung sejak triase terakhir, bukan sejak datang (K11).
    assert item["lama_menunggu_menit"] == 12
    assert item["batas_tunggu_menit"] == 30
    assert item["status_tanda"] == "normal"
    assert item["menunggu_validasi"] is True
    assert item["review_diajukan"] is False


def test_pasien_belum_ditriase_dihitung_sejak_datang(client, perawat, buat_kunjungan):
    buat_kunjungan("Lina", _menit_lalu(sekarang(), 7))
    _, header = perawat
    [item] = client.get(URL, headers=header).get_json()["items"]
    assert item["triase_terakhir"] is None
    assert item["status_tanda"] == "belum_ditriase"
    assert item["lama_menunggu_menit"] == 7
    assert item["batas_tunggu_menit"] is None
    assert (item["menunggu_validasi"], item["review_diajukan"]) == (False, False)


def test_triase_terakhir_yang_dipakai(client, perawat, buat_kunjungan, buat_triase):
    waktu = sekarang()
    kunjungan = buat_kunjungan(waktu_datang=_menit_lalu(waktu, 90))
    buat_triase(kunjungan, RiskLevel.RENDAH, StatusValidasi.DISETUJUI, waktu=_menit_lalu(waktu, 80))
    ulang = buat_triase(kunjungan, RiskLevel.TINGGI, StatusValidasi.MENUNGGU_REVIEW_DOKTER, waktu=_menit_lalu(waktu, 3))
    _, header = perawat
    [item] = client.get(URL, headers=header).get_json()["items"]
    assert item["triase_terakhir"]["id_triase"] == str(ulang.id_triase)
    assert item["triase_terakhir"]["jenis"] == "ulang"
    assert item["lama_menunggu_menit"] == 3
    assert item["batas_tunggu_menit"] == 10
    assert (item["menunggu_validasi"], item["review_diajukan"]) == (True, True)


def test_hanya_kunjungan_menunggu(client, perawat, buat_kunjungan):
    menunggu = buat_kunjungan("Menunggu")
    buat_kunjungan("Ditangani", status=StatusKunjungan.DITANGANI)
    buat_kunjungan("Selesai", status=StatusKunjungan.SELESAI)
    _, header = perawat
    items = client.get(URL, headers=header).get_json()["items"]
    assert [i["id_kunjungan"] for i in items] == [str(menunggu.id_kunjungan)]


def test_urutan_daftar_tunggu(app, buat_kunjungan, buat_triase):
    waktu = sekarang()

    def pasien(nama, level, menit_triase):
        kunjungan = buat_kunjungan(nama, _menit_lalu(waktu, 120))
        if level is not None:
            buat_triase(kunjungan, level, waktu=_menit_lalu(waktu, menit_triase))
        return nama

    urutan = [
        pasien("kritis lama", RiskLevel.KRITIS, 50),
        pasien("kritis baru", RiskLevel.KRITIS, 2),
        pasien("belum ditriase", None, 0),
        pasien("tinggi lewat batas", RiskLevel.TINGGI, 15),
        pasien("rendah lewat batas lama", RiskLevel.RENDAH, 100),
        pasien("rendah lewat batas", RiskLevel.RENDAH, 61),
        pasien("tinggi", RiskLevel.TINGGI, 5),
        pasien("sedang", RiskLevel.SEDANG, 20),
        pasien("rendah", RiskLevel.RENDAH, 40),
    ]
    hasil = _susun(app, waktu)
    assert [i.pasien.nama for i in hasil] == urutan
    tanda = {i.pasien.nama: i.status_tanda for i in hasil}
    assert tanda["kritis lama"] == "normal"
    assert tanda["tinggi lewat batas"] == tanda["rendah lewat batas"] == "perlu_triase_ulang"
    assert tanda["tinggi"] == tanda["sedang"] == "normal"


@pytest.mark.parametrize(
    ("menit", "tanda"),
    [(30, "normal"), (30.9, "normal"), (31, "perlu_triase_ulang")],
)
def test_batas_tepat_belum_dianggap_lewat(app, buat_kunjungan, buat_triase, menit, tanda):
    waktu = sekarang()
    buat_triase(buat_kunjungan(waktu_datang=_menit_lalu(waktu, 60)), RiskLevel.SEDANG, waktu=_menit_lalu(waktu, menit))
    [item] = _susun(app, waktu)
    assert item.status_tanda == tanda


def test_batas_tunggu_mengikuti_konfigurasi(app, client, perawat, buat_kunjungan, buat_triase, sesi_db):
    waktu = sekarang()
    buat_triase(buat_kunjungan(waktu_datang=_menit_lalu(waktu, 60)), RiskLevel.SEDANG, waktu=_menit_lalu(waktu, 25))
    sesi_db.execute(update(Konfigurasi).values(batas_tunggu_sedang=20))
    sesi_db.commit()
    _, header = perawat
    [item] = client.get(URL, headers=header).get_json()["items"]
    assert (item["batas_tunggu_menit"], item["status_tanda"]) == (20, "perlu_triase_ulang")


def test_waktu_di_masa_depan_tidak_negatif(app, buat_kunjungan):
    waktu = sekarang()
    buat_kunjungan(waktu_datang=waktu + timedelta(minutes=2))
    [item] = _susun(app, waktu)
    assert item.lama_menunggu == 0


@pytest.mark.parametrize(("lama", "batas", "hasil"), [(11, 10, True), (10, 10, False), (500, None, False)])
def test_perlu_triase_ulang(lama, batas, hasil):
    assert DaftarTungguService.perlu_triase_ulang(lama, batas) is hasil


def test_daftar_tunggu_kosong(client, perawat):
    _, header = perawat
    assert client.get(URL, headers=header).get_json()["items"] == []


@pytest.mark.parametrize(("peran", "status"), [(Peran.DOKTER, 200), (Peran.ADMIN, 403)])
def test_peran_daftar_tunggu(client, masuk, peran, status):
    _, header = masuk(peran)
    assert client.get(URL, headers=header).status_code == status


def test_daftar_tunggu_tanpa_login(client):
    assert client.get(URL).status_code == 401
