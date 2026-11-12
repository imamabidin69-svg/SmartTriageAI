"""GET /peringatan untuk ICU: menunggu persetujuan dokter, observasi terlambat, informasi penting Eir (FR-07)."""

from datetime import timedelta

import pytest

from app.models import SesiEir
from app.models.enums import PengisiEir, Peran, RiskLevel, StatusKunjungan, StatusSesiEir, StatusValidasi
from app.utils.waktu import sekarang

URL = "/api/v1/peringatan"


@pytest.fixture
def perawat(masuk):
    return masuk(Peran.PERAWAT)


@pytest.fixture
def waktu():
    return sekarang()


def _peringatan(client, header):
    respons = client.get(URL, headers=header)
    assert respons.status_code == 200
    return respons.get_json()["items"]


def _sesi_eir(sesi_db, kunjungan, waktu_selesai, status=StatusSesiEir.SELESAI, informasi="Alergi obat"):
    sesi = SesiEir(
        id_kunjungan=kunjungan.id_kunjungan,
        pengisi=PengisiEir.KELUARGA,
        waktu_persetujuan=waktu_selesai - timedelta(minutes=5),
        status=status,
        tanda_bahaya=informasi,
        waktu_selesai=None if status == StatusSesiEir.BERJALAN else waktu_selesai,
    )
    sesi_db.add(sesi)
    sesi_db.commit()
    return sesi


# ---------------------------------------------------------------- menunggu persetujuan dokter


@pytest.mark.parametrize("status", [StatusValidasi.MENUNGGU, StatusValidasi.MENUNGGU_REVIEW_DOKTER])
def test_penilaian_awal_menunggu_persetujuan(client, perawat, buat_kunjungan, buat_triase, waktu, status):
    kunjungan = buat_kunjungan("Agus")
    triase = buat_triase(kunjungan, RiskLevel.KRITIS, status, waktu=waktu - timedelta(minutes=3))
    _, header = perawat
    [item] = _peringatan(client, header)
    assert item["jenis"] == "menunggu_persetujuan"
    assert item["id_kunjungan"] == str(kunjungan.id_kunjungan)
    assert item["id_triase"] == str(triase.id_triase)
    assert item["id_sesi"] is None
    assert item["pasien"] == {"id_pasien": str(kunjungan.id_pasien), "nama": "Agus"}
    assert item["risk_level"] == "kritis"
    assert item["alasan"] == "Penilaian awal Kritis menunggu persetujuan dokter."


@pytest.mark.parametrize("status", [StatusValidasi.DISETUJUI, StatusValidasi.DIKOREKSI, StatusValidasi.TERCATAT])
def test_penilaian_final_tidak_memicu_peringatan(client, perawat, buat_kunjungan, buat_triase, status):
    buat_triase(buat_kunjungan(), RiskLevel.KRITIS, status)
    _, header = perawat
    assert _peringatan(client, header) == []


def test_persetujuan_lewat_api_menghapus_peringatan(client, masuk, buat_kunjungan, buat_triase):
    triase = buat_triase(buat_kunjungan(), RiskLevel.TINGGI)
    _, header = masuk(Peran.DOKTER)
    assert len(_peringatan(client, header)) == 1
    client.post(f"/api/v1/triase/{triase.id_triase}/validasi", json={"aksi": "setujui"}, headers=header)
    assert _peringatan(client, header) == []


def test_level_naik_menunggu_persetujuan(client, perawat, buat_kunjungan, buat_triase, waktu):
    kunjungan = buat_kunjungan()
    buat_triase(kunjungan, RiskLevel.SEDANG, StatusValidasi.DISETUJUI, waktu=waktu - timedelta(minutes=40))
    ulang = buat_triase(kunjungan, RiskLevel.TINGGI, waktu=waktu - timedelta(minutes=2))
    _, header = perawat
    [item] = _peringatan(client, header)
    assert item["jenis"] == "menunggu_persetujuan"
    assert item["id_triase"] == str(ulang.id_triase)
    assert item["risk_level"] == "tinggi"
    assert item["alasan"] == "Level naik dari Sedang ke Tinggi dan menunggu persetujuan dokter."


def test_level_sama_yang_masih_menunggu(client, perawat, buat_kunjungan, buat_triase, waktu):
    """Kenaikan yang belum disetujui lalu diobservasi lagi dengan level sama tetap muncul."""
    kunjungan = buat_kunjungan()
    buat_triase(kunjungan, RiskLevel.TINGGI, waktu=waktu - timedelta(minutes=20))
    buat_triase(kunjungan, RiskLevel.TINGGI, waktu=waktu - timedelta(minutes=2))
    _, header = perawat
    [item] = _peringatan(client, header)
    assert item["alasan"] == "Level Tinggi belum disetujui dokter."


def test_hanya_observasi_terakhir_yang_dihitung(client, perawat, buat_kunjungan, buat_triase, waktu):
    kunjungan = buat_kunjungan()
    buat_triase(kunjungan, RiskLevel.KRITIS, waktu=waktu - timedelta(minutes=20))
    buat_triase(kunjungan, RiskLevel.RENDAH, StatusValidasi.TERCATAT, waktu=waktu - timedelta(minutes=2))
    _, header = perawat
    assert _peringatan(client, header) == []


# ---------------------------------------------------------------- observasi terlambat


def test_observasi_terlambat(client, perawat, buat_kunjungan, buat_triase, waktu):
    kunjungan = buat_kunjungan("Rina", waktu - timedelta(minutes=200))
    triase = buat_triase(kunjungan, RiskLevel.KRITIS, StatusValidasi.DISETUJUI, waktu=waktu - timedelta(minutes=25))
    _, header = perawat
    [item] = _peringatan(client, header)
    assert item["jenis"] == "observasi_terlambat"
    assert item["id_triase"] == str(triase.id_triase)
    assert item["risk_level"] == "kritis"
    assert item["alasan"] == "Observasi terakhir 25 menit lalu, melewati interval 15 menit untuk level Kritis."


def test_observasi_tepat_waktu_dan_pasien_belum_dinilai_tidak_memicu(
    client, perawat, buat_kunjungan, buat_triase, waktu
):
    buat_triase(buat_kunjungan(), RiskLevel.RENDAH, StatusValidasi.DISETUJUI, waktu=waktu - timedelta(minutes=100))
    buat_kunjungan("Belum dinilai", waktu - timedelta(minutes=500))
    _, header = perawat
    assert _peringatan(client, header) == []


# ---------------------------------------------------------------- informasi penting dari keluarga lewat Eir


@pytest.mark.parametrize("status", [StatusSesiEir.SELESAI, StatusSesiEir.BERJALAN])
def test_informasi_penting_eir(client, perawat, buat_kunjungan, sesi_db, waktu, status):
    kunjungan = buat_kunjungan("Dewi")
    sesi = _sesi_eir(sesi_db, kunjungan, waktu - timedelta(minutes=1), status=status)
    _, header = perawat
    [item] = _peringatan(client, header)
    assert item["jenis"] == "informasi_penting_eir"
    assert item["id_sesi"] == str(sesi.id_sesi)
    assert item["id_triase"] is None
    assert item["risk_level"] is None
    assert item["pasien"]["nama"] == "Dewi"
    assert item["alasan"] == "Informasi penting dari keluarga lewat Eir: Alergi obat"


def test_informasi_penting_hilang_setelah_observasi_baru(client, perawat, buat_kunjungan, buat_triase, sesi_db, waktu):
    kunjungan = buat_kunjungan()
    _sesi_eir(sesi_db, kunjungan, waktu - timedelta(minutes=10))
    buat_triase(kunjungan, RiskLevel.SEDANG, StatusValidasi.DISETUJUI, waktu=waktu - timedelta(minutes=2))
    _, header = perawat
    assert _peringatan(client, header) == []


def test_observasi_sebelum_sesi_tidak_dihitung_tindak_lanjut(
    client, perawat, buat_kunjungan, buat_triase, sesi_db, waktu
):
    kunjungan = buat_kunjungan()
    buat_triase(kunjungan, RiskLevel.RENDAH, StatusValidasi.DISETUJUI, waktu=waktu - timedelta(minutes=30))
    _sesi_eir(sesi_db, kunjungan, waktu - timedelta(minutes=5))
    _, header = perawat
    assert [i["jenis"] for i in _peringatan(client, header)] == ["informasi_penting_eir"]


def test_sesi_tanpa_informasi_penting_tidak_memicu(client, perawat, buat_kunjungan, sesi_db, waktu):
    _sesi_eir(sesi_db, buat_kunjungan(), waktu - timedelta(minutes=1), informasi=None)
    _, header = perawat
    assert _peringatan(client, header) == []


# ---------------------------------------------------------------- cakupan dan urutan


def test_pasien_yang_sedang_tindakan_tetap_diperingatkan(client, perawat, buat_kunjungan, buat_triase):
    buat_triase(buat_kunjungan(status=StatusKunjungan.DITANGANI), RiskLevel.KRITIS)
    _, header = perawat
    assert len(_peringatan(client, header)) == 1


def test_pasien_yang_keluar_icu_tidak_diperingatkan(client, perawat, buat_kunjungan, buat_triase, sesi_db, waktu):
    kunjungan = buat_kunjungan(status=StatusKunjungan.SELESAI)
    buat_triase(kunjungan, RiskLevel.KRITIS)
    _sesi_eir(sesi_db, kunjungan, waktu - timedelta(minutes=1))
    _, header = perawat
    assert _peringatan(client, header) == []


def test_urutan_kritis_menunggu_dulu_lalu_per_jenis(client, masuk, buat_kunjungan, buat_triase, sesi_db, waktu):
    naik = buat_kunjungan("naik")
    buat_triase(naik, RiskLevel.RENDAH, StatusValidasi.DISETUJUI, waktu=waktu - timedelta(minutes=50))
    buat_triase(naik, RiskLevel.SEDANG, waktu=waktu - timedelta(minutes=1))
    buat_triase(buat_kunjungan("kritis lama"), RiskLevel.KRITIS, waktu=waktu - timedelta(minutes=12))
    buat_triase(buat_kunjungan("kritis baru"), RiskLevel.KRITIS, waktu=waktu - timedelta(minutes=10))
    terlambat = buat_kunjungan("terlambat")
    buat_triase(terlambat, RiskLevel.TINGGI, StatusValidasi.DISETUJUI, waktu=waktu - timedelta(minutes=45))
    _sesi_eir(sesi_db, buat_kunjungan("eir"), waktu - timedelta(minutes=5))

    _, header = masuk(Peran.DOKTER)
    assert [i["pasien"]["nama"] for i in _peringatan(client, header)] == [
        "kritis baru",
        "kritis lama",
        "naik",
        "terlambat",
        "eir",
    ]


def test_admin_tidak_menerima_peringatan(client, masuk):
    _, header = masuk(Peran.ADMIN)
    assert client.get(URL, headers=header).status_code == 403


def test_peringatan_tanpa_login(client):
    assert client.get(URL).status_code == 401
