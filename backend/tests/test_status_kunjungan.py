"""PATCH /kunjungan/{id}/status (FR-07, Desain baris 293, keputusan K9)."""

import uuid
from datetime import datetime, timedelta

import pytest

from app.models.enums import Peran, StatusKunjungan
from app.services import kunjungan_service
from app.utils.errors import Tipe
from app.utils.waktu import sekarang


def _url(kunjungan) -> str:
    return f"/api/v1/kunjungan/{kunjungan.id_kunjungan}/status"


@pytest.fixture
def dokter(masuk):
    return masuk(Peran.DOKTER)


def test_dokter_mulai_memeriksa_pasien(client, dokter, kunjungan, sesi_db, monkeypatch):
    waktu = sekarang().replace(microsecond=0)
    monkeypatch.setattr(kunjungan_service, "sekarang", lambda: waktu)
    _, header = dokter
    respons = client.patch(_url(kunjungan), json={"status": "ditangani"}, headers=header)

    assert respons.status_code == 200
    isi = respons.get_json()
    assert isi["id_kunjungan"] == str(kunjungan.id_kunjungan)
    assert isi["status"] == "ditangani"
    assert datetime.fromisoformat(isi["waktu_ditangani"]) == waktu
    sesi_db.refresh(kunjungan)
    assert (kunjungan.status, kunjungan.waktu_ditangani) == (StatusKunjungan.DITANGANI, waktu)


def test_pemeriksaan_selesai_tidak_mengubah_waktu_ditangani(client, dokter, kunjungan, sesi_db):
    _, header = dokter
    mulai = client.patch(_url(kunjungan), json={"status": "ditangani"}, headers=header).get_json()
    respons = client.patch(_url(kunjungan), json={"status": "selesai"}, headers=header)
    assert respons.status_code == 200
    assert respons.get_json()["status"] == "selesai"
    assert respons.get_json()["waktu_ditangani"] == mulai["waktu_ditangani"]


def test_pasien_batal_diperiksa_langsung_selesai(client, dokter, kunjungan):
    _, header = dokter
    respons = client.patch(_url(kunjungan), json={"status": "selesai"}, headers=header)
    assert respons.status_code == 200
    assert respons.get_json() == {
        "id_kunjungan": str(kunjungan.id_kunjungan),
        "status": "selesai",
        "waktu_ditangani": None,
    }


@pytest.mark.parametrize(
    ("awal", "tujuan"),
    [
        (StatusKunjungan.DITANGANI, "ditangani"),
        (StatusKunjungan.SELESAI, "ditangani"),
        (StatusKunjungan.SELESAI, "selesai"),
    ],
)
def test_perubahan_status_yang_tidak_sah_dibalas_409(client, dokter, buat_kunjungan, sesi_db, awal, tujuan):
    kunjungan = buat_kunjungan(status=awal)
    _, header = dokter
    respons = client.patch(_url(kunjungan), json={"status": tujuan}, headers=header)

    assert respons.status_code == 409
    assert respons.get_json()["type"] == Tipe.KONFLIK
    assert respons.get_json()["detail"] == f"Status kunjungan tidak bisa diubah dari {awal.value} ke {tujuan}."
    sesi_db.refresh(kunjungan)
    assert kunjungan.status == awal


@pytest.mark.parametrize(
    ("isi", "pesan"),
    [
        ({"status": "menunggu"}, "Status harus salah satu dari: 'ditangani', 'selesai'."),
        ({}, "Status wajib diisi."),
    ],
)
def test_isian_status_tidak_valid(client, dokter, kunjungan, isi, pesan):
    _, header = dokter
    respons = client.patch(_url(kunjungan), json=isi, headers=header)
    assert respons.status_code == 422
    assert [e["pesan"] for e in respons.get_json()["errors"]] == [pesan]


@pytest.mark.parametrize("peran", [Peran.PERAWAT, Peran.ADMIN])
def test_hanya_dokter_yang_mengubah_status(client, masuk, kunjungan, peran):
    _, header = masuk(peran)
    assert client.patch(_url(kunjungan), json={"status": "ditangani"}, headers=header).status_code == 403


def test_kunjungan_tidak_ada(client, dokter):
    _, header = dokter
    respons = client.patch(f"/api/v1/kunjungan/{uuid.uuid4()}/status", json={"status": "selesai"}, headers=header)
    assert respons.status_code == 404
    assert respons.get_json()["detail"] == "Kunjungan tidak ditemukan."


def test_pasien_yang_ditangani_keluar_dari_daftar_tunggu(client, dokter, buat_kunjungan, buat_triase):
    kunjungan = buat_kunjungan(waktu_datang=sekarang() - timedelta(minutes=5))
    _, header = dokter
    url_daftar = "/api/v1/daftar-tunggu"
    assert [i["id_kunjungan"] for i in client.get(url_daftar, headers=header).get_json()["items"]] == [
        str(kunjungan.id_kunjungan)
    ]
    client.patch(_url(kunjungan), json={"status": "ditangani"}, headers=header)
    assert client.get(url_daftar, headers=header).get_json()["items"] == []
