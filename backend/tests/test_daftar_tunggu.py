"""Papan prioritas ICU GET /daftar-tunggu dan penanda observasi terlambat (FR-07, Desain 2.7, Gambar 2.19)."""

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import update

from app.models import Konfigurasi, SesiEir
from app.models.enums import PengisiEir, Peran, RiskLevel, StatusKunjungan, StatusSesiEir, StatusValidasi
from app.services.daftar_tunggu_service import DaftarTungguService, ringkasan_eir_siap
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
    kunjungan = buat_kunjungan(
        "Agus", _menit_lalu(waktu, 40), nomor_bed="ICU-4", tanggal_lahir=date(1990, 1, 1), perkiraan_usia=None
    )
    kunjungan.diagnosis_masuk = "Syok sepsis"
    triase = buat_triase(
        kunjungan, RiskLevel.SEDANG, waktu=_menit_lalu(waktu, 12), skor_news2=4, peluang_perburukan=Decimal("0.4812")
    )
    _, header = perawat
    respons = client.get(URL, headers=header)

    assert respons.status_code == 200
    isi = respons.get_json()
    assert datetime.fromisoformat(isi["waktu_server"]).tzinfo is not None
    [item] = isi["items"]
    assert item["id_kunjungan"] == str(kunjungan.id_kunjungan)
    assert item["pasien"]["nama"] == "Agus"
    assert (item["nomor_bed"], item["diagnosis_masuk"], item["status"]) == ("ICU-4", "Syok sepsis", "menunggu")
    # Usia dari tanggal lahir 1 Januari, jadi selalu sudah berulang tahun pada tahun berjalan.
    assert item["pasien"]["usia"] == waktu.year - 1990
    assert datetime.fromisoformat(item["triase_terakhir"].pop("waktu_triase")) == triase.waktu_triase
    assert item["triase_terakhir"] == {
        "id_triase": str(triase.id_triase),
        "jenis": "awal",
        "risk_level": "sedang",
        "status_validasi": "menunggu",
        "skor_news2": 4,
        "peluang_perburukan": 0.4812,
    }
    # Lama dihitung sejak observasi terakhir, bukan sejak masuk ICU (K11).
    assert item["lama_menunggu_menit"] == 12
    assert item["batas_tunggu_menit"] == 60
    assert item["status_tanda"] == "normal"
    assert item["menunggu_validasi"] is True
    assert item["review_diajukan"] is False
    assert item["ringkasan_eir_siap"] is False


def test_pasien_belum_dinilai_dihitung_sejak_masuk(client, perawat, buat_kunjungan):
    buat_kunjungan("Lina", _menit_lalu(sekarang(), 7))
    _, header = perawat
    [item] = client.get(URL, headers=header).get_json()["items"]
    assert item["triase_terakhir"] is None
    assert item["status_tanda"] == "belum_dinilai"
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
    assert item["batas_tunggu_menit"] == 30
    assert (item["menunggu_validasi"], item["review_diajukan"]) == (True, True)


def test_pasien_yang_keluar_icu_tidak_tampil_dan_yang_tindakan_paling_bawah(client, perawat, buat_kunjungan):
    waktu = sekarang()
    tindakan = buat_kunjungan("Ditangani", _menit_lalu(waktu, 30), status=StatusKunjungan.DITANGANI)
    dirawat = buat_kunjungan("Menunggu", _menit_lalu(waktu, 5))
    buat_kunjungan("Selesai", status=StatusKunjungan.SELESAI)
    _, header = perawat
    items = client.get(URL, headers=header).get_json()["items"]
    assert [i["id_kunjungan"] for i in items] == [str(dirawat.id_kunjungan), str(tindakan.id_kunjungan)]
    assert items[1]["status"] == "ditangani"


def test_urutan_daftar_tunggu(app, buat_kunjungan, buat_triase):
    waktu = sekarang()

    def pasien(nama, level, menit, status=StatusValidasi.DISETUJUI, peluang=None, skor=0):
        kunjungan = buat_kunjungan(nama, _menit_lalu(waktu, 300))
        if level is not None:
            buat_triase(
                kunjungan,
                level,
                status,
                waktu=_menit_lalu(waktu, menit),
                peluang_perburukan=None if peluang is None else Decimal(peluang),
                skor_news2=skor,
            )
        return nama

    urutan = [
        pasien("kritis menunggu dokter", RiskLevel.KRITIS, 2, StatusValidasi.MENUNGGU),
        pasien("kritis terlambat", RiskLevel.KRITIS, 20),
        pasien("kritis peluang tinggi", RiskLevel.KRITIS, 5, peluang="0.80", skor=9),
        pasien("kritis skor tinggi", RiskLevel.KRITIS, 5, peluang="0.70", skor=11),
        pasien("kritis skor rendah", RiskLevel.KRITIS, 5, peluang="0.70", skor=7),
        pasien("belum dinilai", None, 0),
        pasien("tinggi terlambat", RiskLevel.TINGGI, 45),
        pasien("tinggi", RiskLevel.TINGGI, 5),
        pasien("sedang", RiskLevel.SEDANG, 20),
        pasien("rendah terlambat", RiskLevel.RENDAH, 121),
        pasien("rendah", RiskLevel.RENDAH, 40),
    ]
    hasil = _susun(app, waktu)
    assert [i.pasien.nama for i in hasil] == urutan
    tanda = {i.pasien.nama: i.status_tanda for i in hasil}
    assert tanda["kritis terlambat"] == tanda["tinggi terlambat"] == tanda["rendah terlambat"] == "observasi_terlambat"
    assert tanda["kritis menunggu dokter"] == tanda["tinggi"] == tanda["sedang"] == "normal"


@pytest.mark.parametrize(
    ("menit", "tanda"),
    [(60, "normal"), (60.9, "normal"), (61, "observasi_terlambat")],
)
def test_batas_tepat_belum_dianggap_lewat(app, buat_kunjungan, buat_triase, menit, tanda):
    waktu = sekarang()
    buat_triase(buat_kunjungan(waktu_datang=_menit_lalu(waktu, 90)), RiskLevel.SEDANG, waktu=_menit_lalu(waktu, menit))
    [item] = _susun(app, waktu)
    assert item.status_tanda == tanda


def test_batas_tunggu_mengikuti_konfigurasi(app, client, perawat, buat_kunjungan, buat_triase, sesi_db):
    waktu = sekarang()
    buat_triase(buat_kunjungan(waktu_datang=_menit_lalu(waktu, 60)), RiskLevel.SEDANG, waktu=_menit_lalu(waktu, 25))
    sesi_db.execute(update(Konfigurasi).values(batas_tunggu_kritis=10, batas_tunggu_tinggi=15, batas_tunggu_sedang=20))
    sesi_db.commit()
    _, header = perawat
    [item] = client.get(URL, headers=header).get_json()["items"]
    assert (item["batas_tunggu_menit"], item["status_tanda"]) == (20, "observasi_terlambat")


def test_waktu_di_masa_depan_tidak_negatif(app, buat_kunjungan):
    waktu = sekarang()
    buat_kunjungan(waktu_datang=waktu + timedelta(minutes=2))
    [item] = _susun(app, waktu)
    assert item.lama_menunggu == 0


@pytest.mark.parametrize(("lama", "batas", "hasil"), [(16, 15, True), (15, 15, False), (500, None, False)])
def test_observasi_terlambat(lama, batas, hasil):
    assert DaftarTungguService.observasi_terlambat(lama, batas) is hasil


def test_daftar_tunggu_kosong(client, perawat):
    _, header = perawat
    assert client.get(URL, headers=header).get_json()["items"] == []


@pytest.mark.parametrize(("peran", "status"), [(Peran.DOKTER, 200), (Peran.ADMIN, 403)])
def test_peran_daftar_tunggu(client, masuk, peran, status):
    _, header = masuk(peran)
    assert client.get(URL, headers=header).status_code == status


def test_daftar_tunggu_tanpa_login(client):
    assert client.get(URL).status_code == 401


# ---------------------------------------------------------------- penanda ringkasan Eir siap (keputusan M4)

RINGKASAN = {
    "kronologi": "Sesak sejak semalam",
    "riwayat_penyakit": "Darah tinggi",
    "obat_rutin": "Amlodipin",
    "alergi": "Tidak ada",
    "informasi_lain": "Tidak disebutkan",
}


def _sesi_eir(sesi_db, kunjungan, mulai, status=StatusSesiEir.SELESAI, ringkasan=RINGKASAN, selesai_menit=5):
    sesi = SesiEir(
        id_kunjungan=kunjungan.id_kunjungan,
        pengisi=PengisiEir.KELUARGA,
        waktu_persetujuan=mulai,
        status=status,
        ringkasan=ringkasan,
        waktu_selesai=None if status == StatusSesiEir.BERJALAN else mulai + timedelta(minutes=selesai_menit),
        transkrip=[],
    )
    sesi_db.add(sesi)
    sesi_db.flush()
    return sesi


def test_ringkasan_eir_siap_setelah_sesi_selesai(client, perawat, buat_kunjungan, buat_triase, sesi_db):
    waktu = sekarang()
    kunjungan = buat_kunjungan("Dewi", _menit_lalu(waktu, 40))
    buat_triase(kunjungan, RiskLevel.RENDAH, waktu=_menit_lalu(waktu, 30))
    _sesi_eir(sesi_db, kunjungan, _menit_lalu(waktu, 20))
    _, header = perawat
    [item] = client.get(URL, headers=header).get_json()["items"]
    assert item["ringkasan_eir_siap"] is True


def test_ringkasan_eir_hilang_setelah_triase_ulang(app, buat_kunjungan, buat_triase, sesi_db):
    waktu = sekarang()
    kunjungan = buat_kunjungan("Dewi", _menit_lalu(waktu, 60))
    buat_triase(kunjungan, RiskLevel.RENDAH, waktu=_menit_lalu(waktu, 50))
    _sesi_eir(sesi_db, kunjungan, _menit_lalu(waktu, 40))
    buat_triase(kunjungan, RiskLevel.SEDANG, waktu=_menit_lalu(waktu, 10))
    [item] = _susun(app, waktu)
    assert item.ringkasan_eir_siap is False


@pytest.mark.parametrize(
    ("status", "ringkasan"),
    [
        (StatusSesiEir.DIHENTIKAN, None),
        (StatusSesiEir.BERJALAN, None),
        (StatusSesiEir.SELESAI, None),
    ],
)
def test_ringkasan_eir_tidak_siap(app, buat_kunjungan, buat_triase, sesi_db, status, ringkasan):
    waktu = sekarang()
    kunjungan = buat_kunjungan("Dewi", _menit_lalu(waktu, 40))
    buat_triase(kunjungan, RiskLevel.RENDAH, waktu=_menit_lalu(waktu, 30))
    _sesi_eir(sesi_db, kunjungan, _menit_lalu(waktu, 20), status=status, ringkasan=ringkasan)
    [item] = _susun(app, waktu)
    assert item.ringkasan_eir_siap is False


def test_ringkasan_eir_mengikuti_sesi_terakhir(app, buat_kunjungan, buat_triase, sesi_db):
    """Sama seperti GET /ringkasan-eir: sesi yang lebih baru (masih berjalan) menggantikan ringkasan lama."""
    waktu = sekarang()
    kunjungan = buat_kunjungan("Dewi", _menit_lalu(waktu, 60))
    buat_triase(kunjungan, RiskLevel.RENDAH, waktu=_menit_lalu(waktu, 50))
    _sesi_eir(sesi_db, kunjungan, _menit_lalu(waktu, 40))
    _sesi_eir(sesi_db, kunjungan, _menit_lalu(waktu, 5), status=StatusSesiEir.BERJALAN, ringkasan=None)
    [item] = _susun(app, waktu)
    assert item.ringkasan_eir_siap is False


def test_ringkasan_eir_tiap_kunjungan_terpisah(app, buat_kunjungan, buat_triase, sesi_db):
    waktu = sekarang()
    dengan_eir = buat_kunjungan("Dewi", _menit_lalu(waktu, 40))
    tanpa_eir = buat_kunjungan("Agus", _menit_lalu(waktu, 40))
    for kunjungan in (dengan_eir, tanpa_eir):
        buat_triase(kunjungan, RiskLevel.RENDAH, waktu=_menit_lalu(waktu, 30))
    _sesi_eir(sesi_db, dengan_eir, _menit_lalu(waktu, 20))
    hasil = {item.pasien.nama: item.ringkasan_eir_siap for item in _susun(app, waktu)}
    assert hasil == {"Dewi": True, "Agus": False}


def test_ringkasan_eir_siap_tanpa_triase():
    """Keluarga bisa memakai Eir sebelum observasi pertama; ringkasannya tetap ditandai siap."""
    sesi = SesiEir(status=StatusSesiEir.SELESAI, ringkasan=RINGKASAN, waktu_selesai=sekarang())
    assert ringkasan_eir_siap(sesi, None) is True
    assert ringkasan_eir_siap(None, None) is False
