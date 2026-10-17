"""GET /pasien/{id}/riwayat dengan paginasi kursor (FR-09, Desain 2.9, keputusan K13 dan D7)."""

import uuid
from datetime import datetime, timedelta

import pytest

from app.models.enums import Peran, RiskLevel, StatusKunjungan, StatusValidasi
from app.utils.kursor import Kursor
from app.utils.waktu import sekarang


def _url(id_pasien) -> str:
    return f"/api/v1/pasien/{id_pasien}/riwayat"


@pytest.fixture
def dokter(masuk):
    return masuk(Peran.DOKTER)


def test_riwayat_dari_semua_kunjungan_terbaru_lebih_dulu(client, dokter, buat_kunjungan, buat_triase, sesi_db):
    waktu = sekarang()
    lama = buat_kunjungan("Rina", waktu - timedelta(days=30), StatusKunjungan.SELESAI, nik="3577010101900002")
    t1 = buat_triase(lama, RiskLevel.SEDANG, StatusValidasi.DISETUJUI, waktu=waktu - timedelta(days=30))
    baru = sesi_db.merge(lama.__class__(id_pasien=lama.id_pasien, waktu_datang=waktu - timedelta(hours=1)))
    sesi_db.commit()
    t2 = buat_triase(baru, RiskLevel.RENDAH, waktu=waktu - timedelta(minutes=50))
    t3 = buat_triase(baru, RiskLevel.TINGGI, waktu=waktu - timedelta(minutes=5))

    _, header = dokter
    respons = client.get(_url(lama.id_pasien), headers=header)
    assert respons.status_code == 200
    isi = respons.get_json()
    assert isi["pasien"]["nama"] == "Rina"
    assert "3577010101900002" not in respons.get_data(as_text=True)
    assert "no_telepon" not in respons.get_data(as_text=True)
    assert [i["id_triase"] for i in isi["items"]] == [str(t3.id_triase), str(t2.id_triase), str(t1.id_triase)]
    assert [i["jenis"] for i in isi["items"]] == ["ulang", "awal", "awal"]
    assert isi["items"][2]["kunjungan"]["status"] == "selesai"
    assert isi["items"][0]["kunjungan"]["id_kunjungan"] == str(baru.id_kunjungan)
    assert isi["items"][0]["tanda_vital"]["saturasi"] == 98.0
    assert isi["items"][2]["status_validasi"] == "disetujui"
    assert isi["kursor_berikutnya"] is None


def test_paginasi_kursor(client, dokter, buat_kunjungan, buat_triase):
    waktu = sekarang()
    kunjungan = buat_kunjungan()
    triase = [buat_triase(kunjungan, waktu=waktu - timedelta(minutes=m)) for m in range(5)]
    # Dua triase dengan waktu sama tetap terurut stabil lewat id.
    kembar = buat_triase(kunjungan, waktu=triase[2].waktu_triase)
    urutan = sorted([*triase, kembar], key=lambda t: (t.waktu_triase, str(t.id_triase)), reverse=True)

    _, header = dokter
    terbaca, kursor = [], None
    for _ in range(4):
        query = {"ukuran": 2, **({"kursor": kursor} if kursor else {})}
        isi = client.get(_url(kunjungan.id_pasien), query_string=query, headers=header).get_json()
        terbaca += [i["id_triase"] for i in isi["items"]]
        kursor = isi["kursor_berikutnya"]
        if kursor is None:
            break
    assert terbaca == [str(t.id_triase) for t in urutan]


def test_pasien_tanpa_triase(client, dokter, buat_kunjungan):
    kunjungan = buat_kunjungan()
    _, header = dokter
    isi = client.get(_url(kunjungan.id_pasien), headers=header).get_json()
    assert (isi["items"], isi["kursor_berikutnya"]) == ([], None)


@pytest.mark.parametrize(
    "kursor",
    [
        "bukan-base64!",
        "eyJ3IjoiMjAyNiJ9",
        # Waktu tanpa zona.
        Kursor(datetime(2026, 1, 1), uuid.uuid4()).enkode(),
        "eyJ3IjoiMjAyNi0wMS0wMVQwMDowMDowMCIsImkiOiJhIn0",
    ],
)
def test_kursor_rusak_ditolak(client, dokter, buat_kunjungan, kursor):
    kunjungan = buat_kunjungan()
    _, header = dokter
    respons = client.get(_url(kunjungan.id_pasien), query_string={"kursor": kursor}, headers=header)
    assert respons.status_code == 422
    assert respons.get_json()["errors"] == [
        {"field": "kursor", "pesan": "Kursor tidak valid. Muat ulang dari halaman pertama."}
    ]


def test_kursor_bolak_balik():
    posisi = Kursor(sekarang(), uuid.uuid4())
    assert Kursor.dekode(posisi.enkode()) == posisi


@pytest.mark.parametrize(("ukuran", "pesan"), [(0, "Ukuran halaman minimal 1."), (51, "Ukuran halaman maksimal 50.")])
def test_ukuran_halaman_dibatasi(client, dokter, buat_kunjungan, ukuran, pesan):
    _, header = dokter
    respons = client.get(_url(buat_kunjungan().id_pasien), query_string={"ukuran": ukuran}, headers=header)
    assert [e["pesan"] for e in respons.get_json()["errors"]] == [pesan]


def test_pasien_tidak_ada(client, dokter):
    _, header = dokter
    respons = client.get(_url(uuid.uuid4()), headers=header)
    assert respons.status_code == 404
    assert respons.get_json()["detail"] == "Pasien tidak ditemukan."


@pytest.mark.parametrize(("peran", "status"), [(Peran.PERAWAT, 200), (Peran.ADMIN, 403)])
def test_peran_riwayat(client, masuk, buat_kunjungan, peran, status):
    _, header = masuk(peran)
    assert client.get(_url(buat_kunjungan().id_pasien), headers=header).status_code == status
