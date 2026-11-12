"""GET dan PATCH /admin/konfigurasi (ambang NEWS2 dan interval observasi ICU), cache, dan audit (FR-05, NFR-06)."""

from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models import Konfigurasi, LogAudit
from app.models.enums import AksiAudit, Peran, RiskLevel
from app.services.konfigurasi_service import CacheKonfigurasi, KonfigurasiTidakAdaError, NilaiKonfigurasi
from app.utils.errors import Tipe

URL = "/api/v1/admin/konfigurasi"


def _log_konfigurasi(sesi_db):
    return sesi_db.scalars(select(LogAudit).where(LogAudit.aksi == AksiAudit.UBAH_KONFIGURASI)).all()


def test_admin_membaca_konfigurasi_bawaan(client, masuk):
    _, header = masuk(Peran.ADMIN)
    respons = client.get(URL, headers=header)
    assert respons.status_code == 200
    assert respons.get_json() == {
        "versi_model": "rf-icu-physionet2019-v1",
        "ambang_kritis": 7,
        "ambang_tinggi": 5,
        "ambang_sedang": 3,
        "batas_tunggu_kritis": 15,
        "batas_tunggu_tinggi": 30,
        "batas_tunggu_sedang": 60,
        "batas_tunggu_rendah": 120,
        "ambang_keyakinan": 0.85,
        "versi_model_termuat": "rf-icu-physionet2019-v1",
    }


@pytest.mark.parametrize("peran", [Peran.PERAWAT, Peran.DOKTER])
def test_hanya_admin_yang_boleh(client, masuk, peran):
    _, header = masuk(peran)
    assert client.get(URL, headers=header).status_code == 403
    assert client.patch(URL, json={"ambang_kritis": 8}, headers=header).status_code == 403


def test_patch_sebagian_mengubah_dan_mencatat_audit(client, masuk, sesi_db):
    admin, header = masuk(Peran.ADMIN)
    respons = client.patch(URL, json={"batas_tunggu_sedang": 45, "ambang_kritis": 8}, headers=header)

    assert respons.status_code == 200
    isi = respons.get_json()
    assert isi["batas_tunggu_sedang"] == 45
    assert isi["ambang_kritis"] == 8
    assert isi["ambang_tinggi"] == 5
    baris = sesi_db.get(Konfigurasi, 1)
    sesi_db.refresh(baris)
    assert (baris.batas_tunggu_sedang, baris.ambang_kritis) == (45, 8)

    [log] = _log_konfigurasi(sesi_db)
    assert log.id_aktor == admin.id_pengguna
    assert log.id_triase is None
    # Urutan catatan mengikuti urutan kolom, bukan urutan field di request.
    assert log.catatan == "ambang_kritis: 7 -> 8; batas_tunggu_sedang: 60 -> 45"


def test_patch_tanpa_perubahan_tidak_dicatat(client, masuk, sesi_db):
    _, header = masuk(Peran.ADMIN)
    respons = client.patch(URL, json={"ambang_kritis": 7, "ambang_keyakinan": 0.85}, headers=header)
    assert respons.status_code == 200
    assert _log_konfigurasi(sesi_db) == []


def test_ambang_keyakinan_desimal(client, masuk, sesi_db):
    _, header = masuk(Peran.ADMIN)
    respons = client.patch(URL, json={"ambang_keyakinan": "0.9"}, headers=header)
    assert respons.get_json()["ambang_keyakinan"] == 0.9
    [log] = _log_konfigurasi(sesi_db)
    # Ditulis dua desimal seperti kolom NUMERIC(3,2), apa pun bentuk angka yang dikirim klien.
    assert log.catatan == "ambang_keyakinan: 0.85 -> 0.90"


def test_patch_kosong_ditolak(client, masuk):
    _, header = masuk(Peran.ADMIN)
    respons = client.patch(URL, json={}, headers=header)
    assert respons.status_code == 422
    assert respons.get_json()["errors"] == [
        {"field": "body", "pesan": "Isi minimal satu pengaturan yang ingin diubah."}
    ]


@pytest.mark.parametrize(
    ("isi", "errors"),
    [
        (
            {"ambang_tinggi": 7},
            [
                {
                    "field": "ambang_tinggi",
                    "pesan": "Ambang NEWS2 tinggi harus lebih kecil dari ambang NEWS2 kritis (7).",
                }
            ],
        ),
        (
            {"ambang_kritis": 4},
            [
                {
                    "field": "ambang_kritis",
                    "pesan": "Ambang NEWS2 kritis harus lebih besar dari ambang NEWS2 tinggi (5).",
                }
            ],
        ),
        (
            {"ambang_sedang": 6},
            [
                {
                    "field": "ambang_sedang",
                    "pesan": "Ambang NEWS2 sedang harus lebih kecil dari ambang NEWS2 tinggi (5).",
                }
            ],
        ),
        (
            {"ambang_kritis": 5, "ambang_tinggi": 5},
            [
                {
                    "field": "ambang_kritis",
                    "pesan": "Ambang NEWS2 kritis harus lebih besar dari ambang NEWS2 tinggi (5).",
                }
            ],
        ),
        (
            {"batas_tunggu_kritis": 40},
            [
                {
                    "field": "batas_tunggu_kritis",
                    "pesan": (
                        "Interval observasi kritis tidak boleh lebih besar dari interval observasi tinggi (30 menit)."
                    ),
                }
            ],
        ),
        (
            {"batas_tunggu_tinggi": 90},
            [
                {
                    "field": "batas_tunggu_tinggi",
                    "pesan": (
                        "Interval observasi tinggi tidak boleh lebih besar dari interval observasi sedang (60 menit)."
                    ),
                }
            ],
        ),
        (
            {"batas_tunggu_rendah": 45},
            [
                {
                    "field": "batas_tunggu_rendah",
                    "pesan": (
                        "Interval observasi rendah tidak boleh lebih kecil dari interval observasi sedang (60 menit)."
                    ),
                }
            ],
        ),
    ],
)
def test_urutan_ambang_dan_batas_tunggu_diperiksa(client, masuk, sesi_db, isi, errors):
    _, header = masuk(Peran.ADMIN)
    respons = client.patch(URL, json=isi, headers=header)
    assert respons.status_code == 422
    assert respons.content_type == "application/problem+json"
    assert respons.get_json()["type"] == Tipe.VALIDASI
    assert respons.get_json()["errors"] == errors
    assert _log_konfigurasi(sesi_db) == []


def test_batas_tunggu_boleh_sama_antar_level(client, masuk):
    _, header = masuk(Peran.ADMIN)
    respons = client.patch(URL, json={"batas_tunggu_kritis": 30, "batas_tunggu_sedang": 30}, headers=header)
    assert respons.status_code == 200


@pytest.mark.parametrize(
    ("isi", "pesan"),
    [
        ({"ambang_kritis": 21}, "Ambang NEWS2 kritis maksimal 20."),
        ({"ambang_sedang": 0}, "Ambang NEWS2 sedang minimal 1."),
        ({"batas_tunggu_rendah": 1441}, "Interval observasi rendah maksimal 1440 menit."),
        ({"batas_tunggu_kritis": 0}, "Interval observasi kritis minimal 1 menit."),
        ({"ambang_keyakinan": 1.5}, "Ambang keyakinan maksimal 1."),
        ({"ambang_keyakinan": 0.855}, "Ambang keyakinan maksimal 2 angka di belakang koma."),
        # Admin yang mengira nilainya persen tetap mendapat pesan batas yang jelas.
        ({"ambang_keyakinan": 85}, "Ambang keyakinan maksimal 1."),
        ({"ambang_keyakinan": 0.30000000000000004}, "Ambang keyakinan maksimal 2 angka di belakang koma."),
        ({"ambang_kritis": None}, "Ambang NEWS2 kritis harus berupa bilangan bulat."),
        ({"ambang_kritis": 6.5}, "Ambang NEWS2 kritis harus berupa bilangan bulat."),
        ({"versi_model": ""}, "Versi model wajib diisi."),
    ],
)
def test_batas_nilai_konfigurasi(client, masuk, isi, pesan):
    _, header = masuk(Peran.ADMIN)
    respons = client.patch(URL, json=isi, headers=header)
    assert respons.status_code == 422
    assert [e["pesan"] for e in respons.get_json()["errors"]] == [pesan]


def test_versi_model_harus_sama_dengan_model_termuat(client, masuk):
    _, header = masuk(Peran.ADMIN)
    respons = client.patch(URL, json={"versi_model": "smarttriage-rf-v2.0.0"}, headers=header)
    assert respons.status_code == 422
    assert respons.get_json()["errors"] == [
        {
            "field": "versi_model",
            "pesan": "Versi model harus sama dengan model yang sedang dimuat (rf-icu-physionet2019-v1).",
        }
    ]


def test_versi_model_tidak_bisa_diubah_tanpa_model(app_tanpa_model, buat_pengguna):
    from bantuan import header_masuk

    klien = app_tanpa_model.test_client()
    header = header_masuk(klien, buat_pengguna(Peran.ADMIN).email)
    respons = klien.patch(URL, json={"versi_model": "rf-icu-physionet2019-v1"}, headers=header)
    assert respons.status_code == 422
    assert respons.get_json()["errors"][0]["pesan"] == (
        "Model perburukan belum dimuat, jadi versi model belum bisa diubah."
    )
    assert klien.get(URL, headers=header).get_json()["versi_model_termuat"] is None


# ---------------------------------------------------------------- cache


class _Jam:
    def __init__(self):
        self.waktu = 1000.0

    def __call__(self):
        return self.waktu


def test_cache_menyimpan_nilai_sampai_kedaluwarsa(sesi_db):
    jam = _Jam()
    cache = CacheKonfigurasi(60, jam=jam)
    assert cache.ambil().ambang_kritis == 7

    baris = sesi_db.get(Konfigurasi, 1)
    baris.ambang_kritis = 9
    sesi_db.commit()
    jam.waktu += 59
    assert cache.ambil().ambang_kritis == 7
    jam.waktu += 1
    assert cache.ambil().ambang_kritis == 9


def test_cache_dikosongkan_setelah_patch(app, client, masuk, monkeypatch):
    cache = CacheKonfigurasi(3600)
    monkeypatch.setitem(app.extensions, "cache_konfigurasi", cache)
    _, header = masuk(Peran.ADMIN)
    assert client.get(URL, headers=header).get_json()["ambang_kritis"] == 7
    client.patch(URL, json={"ambang_kritis": 8}, headers=header)
    assert client.get(URL, headers=header).get_json()["ambang_kritis"] == 8


def test_cache_tanpa_baris_konfigurasi(sesi_db):
    sesi_db.delete(sesi_db.get(Konfigurasi, 1))
    sesi_db.flush()
    with pytest.raises(KonfigurasiTidakAdaError):
        CacheKonfigurasi(0).ambil()


def test_interval_observasi_per_level():
    nilai = NilaiKonfigurasi("v", 7, 5, 3, 15, 30, 60, 120, Decimal("0.85"))
    assert nilai.batas_tunggu(RiskLevel.KRITIS) == 15
    assert nilai.batas_tunggu(RiskLevel.TINGGI) == 30
    assert nilai.batas_tunggu(RiskLevel.SEDANG) == 60
    assert nilai.batas_tunggu(RiskLevel.RENDAH) == 120
    ambang = nilai.ambang_news2
    assert (ambang.kritis, ambang.tinggi, ambang.sedang) == (7, 5, 3)
