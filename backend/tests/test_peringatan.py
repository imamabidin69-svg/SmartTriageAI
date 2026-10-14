"""GET /peringatan (FR-07, Desain baris 293, keputusan K10, U4, dan U5)."""

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


def _sesi_eir(sesi_db, kunjungan, waktu_selesai, status=StatusSesiEir.DIHENTIKAN, tanda_bahaya="nyeri dada hebat"):
    sesi = SesiEir(
        id_kunjungan=kunjungan.id_kunjungan,
        pengisi=PengisiEir.PASIEN,
        waktu_persetujuan=waktu_selesai - timedelta(minutes=5),
        status=status,
        tanda_bahaya=tanda_bahaya,
        waktu_selesai=waktu_selesai,
    )
    sesi_db.add(sesi)
    sesi_db.commit()
    return sesi


# ---------------------------------------------------------------- kritis belum divalidasi


@pytest.mark.parametrize("status", [StatusValidasi.MENUNGGU, StatusValidasi.MENUNGGU_REVIEW_DOKTER])
def test_triase_kritis_belum_divalidasi(client, perawat, buat_kunjungan, buat_triase, waktu, status):
    kunjungan = buat_kunjungan("Agus")
    triase = buat_triase(kunjungan, RiskLevel.KRITIS, status, waktu=waktu - timedelta(minutes=3))
    _, header = perawat
    [item] = _peringatan(client, header)
    assert item["jenis"] == "kritis_belum_divalidasi"
    assert item["id_kunjungan"] == str(kunjungan.id_kunjungan)
    assert item["id_triase"] == str(triase.id_triase)
    assert item["id_sesi"] is None
    assert item["pasien"] == {"id_pasien": str(kunjungan.id_pasien), "nama": "Agus"}
    assert item["risk_level"] == "kritis"
    assert item["alasan"] == "Hasil triase kritis belum divalidasi."


@pytest.mark.parametrize("status", [StatusValidasi.DISETUJUI, StatusValidasi.DIKOREKSI])
def test_peringatan_kritis_hilang_setelah_divalidasi(client, perawat, buat_kunjungan, buat_triase, status):
    buat_triase(buat_kunjungan(), RiskLevel.KRITIS, status)
    _, header = perawat
    assert _peringatan(client, header) == []


def test_validasi_lewat_api_menghapus_peringatan(client, masuk, buat_kunjungan, buat_triase):
    triase = buat_triase(buat_kunjungan(), RiskLevel.KRITIS)
    _, header = masuk(Peran.DOKTER)
    assert len(_peringatan(client, header)) == 1
    client.post(f"/api/v1/triase/{triase.id_triase}/validasi", json={"aksi": "setujui"}, headers=header)
    assert _peringatan(client, header) == []


@pytest.mark.parametrize("level", [RiskLevel.RENDAH, RiskLevel.SEDANG, RiskLevel.TINGGI])
def test_triase_awal_non_kritis_tidak_memicu_peringatan(client, perawat, buat_kunjungan, buat_triase, level):
    buat_triase(buat_kunjungan(), level)
    _, header = perawat
    assert _peringatan(client, header) == []


# ---------------------------------------------------------------- level naik


def test_triase_ulang_yang_levelnya_naik(client, perawat, buat_kunjungan, buat_triase, waktu):
    kunjungan = buat_kunjungan()
    buat_triase(kunjungan, RiskLevel.SEDANG, StatusValidasi.DISETUJUI, waktu=waktu - timedelta(minutes=40))
    ulang = buat_triase(kunjungan, RiskLevel.TINGGI, waktu=waktu - timedelta(minutes=2))
    _, header = perawat
    [item] = _peringatan(client, header)
    assert item["jenis"] == "level_naik"
    assert item["id_triase"] == str(ulang.id_triase)
    assert item["risk_level"] == "tinggi"
    assert item["alasan"] == "Triase ulang naik dari sedang ke tinggi dan belum divalidasi."


def test_level_naik_ke_kritis_hanya_satu_peringatan(client, perawat, buat_kunjungan, buat_triase, waktu):
    kunjungan = buat_kunjungan()
    buat_triase(kunjungan, RiskLevel.SEDANG, waktu=waktu - timedelta(minutes=40))
    buat_triase(kunjungan, RiskLevel.KRITIS, waktu=waktu - timedelta(minutes=2))
    _, header = perawat
    [item] = _peringatan(client, header)
    assert item["jenis"] == "kritis_belum_divalidasi"
    assert item["alasan"] == "Triase ulang naik dari sedang ke kritis dan belum divalidasi."


@pytest.mark.parametrize(
    ("awal", "ulang", "status_ulang"),
    [
        (RiskLevel.TINGGI, RiskLevel.SEDANG, StatusValidasi.MENUNGGU),
        (RiskLevel.SEDANG, RiskLevel.SEDANG, StatusValidasi.MENUNGGU),
        (RiskLevel.SEDANG, RiskLevel.TINGGI, StatusValidasi.DISETUJUI),
        # Hanya triase terakhir yang dihitung: kritis lama yang sudah turun tidak memicu peringatan.
        (RiskLevel.KRITIS, RiskLevel.RENDAH, StatusValidasi.MENUNGGU),
    ],
)
def test_level_turun_tetap_atau_sudah_divalidasi(
    client, perawat, buat_kunjungan, buat_triase, waktu, awal, ulang, status_ulang
):
    kunjungan = buat_kunjungan()
    buat_triase(kunjungan, awal, waktu=waktu - timedelta(minutes=40))
    buat_triase(kunjungan, ulang, status_ulang, waktu=waktu - timedelta(minutes=2))
    _, header = perawat
    assert _peringatan(client, header) == []


def test_level_dibanding_triase_tepat_sebelumnya(client, perawat, buat_kunjungan, buat_triase, waktu):
    kunjungan = buat_kunjungan()
    buat_triase(kunjungan, RiskLevel.RENDAH, waktu=waktu - timedelta(minutes=60))
    buat_triase(kunjungan, RiskLevel.TINGGI, waktu=waktu - timedelta(minutes=30))
    buat_triase(kunjungan, RiskLevel.TINGGI, waktu=waktu - timedelta(minutes=2))
    _, header = perawat
    assert _peringatan(client, header) == []


# ---------------------------------------------------------------- tanda bahaya Eir


def test_sesi_eir_dihentikan_karena_tanda_bahaya(client, perawat, buat_kunjungan, sesi_db, waktu):
    kunjungan = buat_kunjungan("Dewi")
    sesi = _sesi_eir(sesi_db, kunjungan, waktu - timedelta(minutes=1))
    _, header = perawat
    [item] = _peringatan(client, header)
    assert item["jenis"] == "tanda_bahaya_eir"
    assert item["id_sesi"] == str(sesi.id_sesi)
    assert item["id_triase"] is None
    assert item["risk_level"] is None
    assert item["pasien"]["nama"] == "Dewi"
    assert item["alasan"] == "Eir menghentikan sesi karena tanda bahaya: nyeri dada hebat"


def test_tanda_bahaya_hilang_setelah_ada_triase_baru(client, perawat, buat_kunjungan, buat_triase, sesi_db, waktu):
    kunjungan = buat_kunjungan()
    _sesi_eir(sesi_db, kunjungan, waktu - timedelta(minutes=10))
    buat_triase(kunjungan, RiskLevel.SEDANG, StatusValidasi.DISETUJUI, waktu=waktu - timedelta(minutes=2))
    _, header = perawat
    assert _peringatan(client, header) == []


def test_triase_sebelum_sesi_tidak_dihitung_tindak_lanjut(client, perawat, buat_kunjungan, buat_triase, sesi_db, waktu):
    kunjungan = buat_kunjungan()
    buat_triase(kunjungan, RiskLevel.RENDAH, StatusValidasi.DISETUJUI, waktu=waktu - timedelta(minutes=30))
    _sesi_eir(sesi_db, kunjungan, waktu - timedelta(minutes=5))
    _, header = perawat
    assert [i["jenis"] for i in _peringatan(client, header)] == ["tanda_bahaya_eir"]


@pytest.mark.parametrize(
    ("status", "tanda_bahaya"),
    [(StatusSesiEir.SELESAI, None), (StatusSesiEir.BERJALAN, None), (StatusSesiEir.DIHENTIKAN, None)],
)
def test_sesi_tanpa_tanda_bahaya_tidak_memicu_peringatan(
    client, perawat, buat_kunjungan, sesi_db, waktu, status, tanda_bahaya
):
    _sesi_eir(sesi_db, buat_kunjungan(), waktu - timedelta(minutes=1), status=status, tanda_bahaya=tanda_bahaya)
    _, header = perawat
    assert _peringatan(client, header) == []


# ---------------------------------------------------------------- cakupan dan urutan


@pytest.mark.parametrize("status", [StatusKunjungan.DITANGANI, StatusKunjungan.SELESAI])
def test_hanya_kunjungan_yang_masih_menunggu(client, perawat, buat_kunjungan, buat_triase, sesi_db, waktu, status):
    kunjungan = buat_kunjungan(status=status)
    buat_triase(kunjungan, RiskLevel.KRITIS)
    _sesi_eir(sesi_db, kunjungan, waktu - timedelta(minutes=1))
    _, header = perawat
    assert _peringatan(client, header) == []


def test_urutan_kritis_dulu_lalu_terbaru(client, masuk, buat_kunjungan, buat_triase, sesi_db, waktu):
    naik = buat_kunjungan("naik")
    buat_triase(naik, RiskLevel.RENDAH, waktu=waktu - timedelta(minutes=50))
    buat_triase(naik, RiskLevel.SEDANG, waktu=waktu - timedelta(minutes=1))
    buat_triase(buat_kunjungan("kritis lama"), RiskLevel.KRITIS, waktu=waktu - timedelta(minutes=30))
    buat_triase(buat_kunjungan("kritis baru"), RiskLevel.KRITIS, waktu=waktu - timedelta(minutes=10))
    _sesi_eir(sesi_db, buat_kunjungan("eir"), waktu - timedelta(minutes=5))

    _, header = masuk(Peran.DOKTER)
    assert [i["pasien"]["nama"] for i in _peringatan(client, header)] == ["kritis baru", "kritis lama", "naik", "eir"]


def test_admin_tidak_menerima_peringatan(client, masuk):
    _, header = masuk(Peran.ADMIN)
    assert client.get(URL, headers=header).status_code == 403


def test_peringatan_tanpa_login(client):
    assert client.get(URL).status_code == 401
