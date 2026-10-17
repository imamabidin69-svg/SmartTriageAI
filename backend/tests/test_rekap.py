"""GET /rekap dan ekspor CSV (FR-09, Desain 2.9, keputusan K12, V1, V2, D8)."""

from datetime import date, datetime, time, timedelta

import pytest

from app.models.enums import JenisTriase, Peran, RiskLevel, StatusKunjungan, StatusValidasi
from app.services.rekap_service import PenulisCsv, Rekap, rentang_tanggal
from app.utils.errors import ValidasiGagalError
from app.utils.waktu import WIB, hari_ini

URL = "/api/v1/rekap"
HARI = date(2026, 3, 10)


def _jam(hari: date, jam: int, menit: int = 0) -> datetime:
    return datetime.combine(hari, time(jam, menit), WIB)


@pytest.fixture
def admin(masuk):
    return masuk(Peran.ADMIN)


@pytest.fixture
def data_rekap(buat_kunjungan, buat_triase):
    """Tiga kunjungan pada HARI, satu kunjungan sehari sebelumnya, dan satu sehari sesudahnya."""
    # Datang 08.00, ditangani 08.30 (30 menit), triase awal sedang lalu ulang tinggi yang dikoreksi.
    a = buat_kunjungan("A", _jam(HARI, 8), StatusKunjungan.DITANGANI)
    a.waktu_ditangani = _jam(HARI, 8, 30)
    buat_triase(a, RiskLevel.SEDANG, StatusValidasi.DISETUJUI, waktu=_jam(HARI, 8, 5))
    buat_triase(a, RiskLevel.TINGGI, StatusValidasi.DIKOREKSI, waktu=_jam(HARI, 8, 20))
    # Datang 09.00, ditangani 09.10 (10 menit), tinggi.
    b = buat_kunjungan("B", _jam(HARI, 9), StatusKunjungan.SELESAI)
    b.waktu_ditangani = _jam(HARI, 9, 10)
    buat_triase(b, RiskLevel.TINGGI, StatusValidasi.DISETUJUI, waktu=_jam(HARI, 9, 2))
    # Masih menunggu, rendah. Tidak ikut rata-rata tunggu.
    c = buat_kunjungan("C", _jam(HARI, 23, 50))
    buat_triase(c, RiskLevel.RENDAH, waktu=_jam(HARI, 23, 55))
    # Di luar rentang (batas hari WIB).
    buat_triase(
        buat_kunjungan("D", _jam(HARI, 0) - timedelta(minutes=10)),
        RiskLevel.KRITIS,
        waktu=_jam(HARI, 0) - timedelta(minutes=5),
    )
    buat_triase(
        buat_kunjungan("E", _jam(HARI + timedelta(days=1), 0)),
        RiskLevel.KRITIS,
        waktu=_jam(HARI + timedelta(days=1), 0),
    )


def test_rekap_satu_hari(client, admin, data_rekap, sesi_db):
    sesi_db.commit()
    _, header = admin
    respons = client.get(URL, query_string={"dari": HARI.isoformat(), "sampai": HARI.isoformat()}, headers=header)

    assert respons.status_code == 200
    assert respons.get_json() == {
        "dari": "2026-03-10",
        "sampai": "2026-03-10",
        "total_triase": 4,
        "per_level": {"rendah": 1, "sedang": 1, "tinggi": 2, "kritis": 0},
        # Menurut level triase terakhir kunjungan: A dan B sama-sama tinggi, (30 + 10) / 2 = 20.
        "rata_tunggu_menit": {"rendah": None, "sedang": None, "tinggi": 20.0, "kritis": None},
        "persen_koreksi": 25.0,
        "triase_ulang": 1,
        "akurasi_pemindaian": None,
    }


def test_rentang_lebih_lebar_menghitung_semua(client, admin, data_rekap):
    _, header = admin
    query = {"dari": (HARI - timedelta(days=1)).isoformat(), "sampai": (HARI + timedelta(days=1)).isoformat()}
    isi = client.get(URL, query_string=query, headers=header).get_json()
    assert isi["total_triase"] == 6
    assert isi["per_level"]["kritis"] == 2
    assert isi["persen_koreksi"] == round(1 / 6 * 100, 1)


def test_rekap_kosong(client, admin):
    _, header = admin
    isi = client.get(URL, query_string={"dari": "2020-01-01", "sampai": "2020-01-02"}, headers=header).get_json()
    assert isi["total_triase"] == 0
    assert isi["per_level"] == {"rendah": 0, "sedang": 0, "tinggi": 0, "kritis": 0}
    assert isi["persen_koreksi"] is None


def test_rentang_bawaan_tujuh_hari_terakhir(client, admin):
    _, header = admin
    isi = client.get(URL, headers=header).get_json()
    assert isi["sampai"] == hari_ini().isoformat()
    assert isi["dari"] == (hari_ini() - timedelta(days=6)).isoformat()


@pytest.mark.parametrize(
    ("dari", "sampai", "hasil"),
    [
        (None, date(2026, 3, 10), (date(2026, 3, 4), date(2026, 3, 10))),
        (date(2026, 1, 1), date(2026, 12, 31), (date(2026, 1, 1), date(2026, 12, 31))),
    ],
)
def test_rentang_tanggal(dari, sampai, hasil):
    assert rentang_tanggal(dari, sampai) == hasil


@pytest.mark.parametrize(
    ("query", "field", "pesan"),
    [
        ({"dari": "2026-03-10", "sampai": "2026-03-09"}, "dari", "Tanggal awal tidak boleh melewati tanggal akhir."),
        ({"dari": "2025-01-01", "sampai": "2026-01-02"}, "sampai", "Rentang tanggal maksimal 366 hari."),
        ({"dari": "10-03-2026"}, "dari", "Tanggal awal harus berupa tanggal dengan format YYYY-MM-DD."),
        ({"format": "xlsx"}, "format", "Format harus salah satu dari: 'json', 'csv'."),
    ],
)
def test_parameter_rekap_tidak_valid(client, admin, query, field, pesan):
    _, header = admin
    respons = client.get(URL, query_string=query, headers=header)
    assert respons.status_code == 422
    assert respons.get_json()["errors"] == [{"field": field, "pesan": pesan}]


@pytest.mark.parametrize("peran", [Peran.PERAWAT, Peran.DOKTER])
def test_rekap_hanya_untuk_admin(client, masuk, peran):
    _, header = masuk(peran)
    assert client.get(URL, headers=header).status_code == 403
    assert client.get(URL, query_string={"format": "csv"}, headers=header).status_code == 403


# ---------------------------------------------------------------- CSV


def test_ekspor_csv(client, admin, data_rekap):
    _, header = admin
    query = {"dari": HARI.isoformat(), "sampai": HARI.isoformat(), "format": "csv"}
    respons = client.get(URL, query_string=query, headers=header)

    assert respons.status_code == 200
    assert respons.mimetype == "text/csv"
    assert respons.headers["Content-Disposition"] == 'attachment; filename="rekap-2026-03-10_2026-03-10.csv"'
    teks = respons.get_data(as_text=True)
    assert teks.startswith("﻿")
    # Agregat saja, tanpa nama pasien; sel kosong berarti belum ada data.
    assert teks[1:].split("\r\n") == [
        "metrik;nilai",
        "Rentang tanggal;2026-03-10 s.d. 2026-03-10",
        "Total triase;4",
        "Triase rendah;1",
        "Triase sedang;1",
        "Triase tinggi;2",
        "Triase kritis;0",
        "Rata-rata tunggu rendah (menit);",
        "Rata-rata tunggu sedang (menit);",
        "Rata-rata tunggu tinggi (menit);20,0",
        "Rata-rata tunggu kritis (menit);",
        "Persen koreksi dokter (%);25,0",
        "Triase ulang;1",
        "Akurasi pemindaian (%);",
        "",
    ]


def test_csv_aman_dari_injeksi_formula_dan_pemisah():
    rekap = Rekap(
        dari=HARI,
        sampai=HARI,
        total_triase=0,
        per_level=dict.fromkeys(RiskLevel, 0),
        rata_tunggu_menit=dict.fromkeys(RiskLevel),
        persen_koreksi=None,
        triase_ulang=0,
        akurasi_pemindaian=None,
    )

    class PenulisUji(PenulisCsv):
        def baris(self, rekap):
            return [("=HYPERLINK(1)", "+1"), ("isi;titik koma", '"kutip"'), ("-2", "@a")]

    teks = "".join(PenulisUji().stream(rekap))
    assert teks.split("\r\n")[1:4] == [
        "'=HYPERLINK(1);'+1",
        '"isi;titik koma";"""kutip"""',
        "'-2;'@a",
    ]


def test_jenis_ulang_dihitung_dari_kolom_jenis(buat_kunjungan, buat_triase, app):
    from app.services.rekap_service import RekapService

    kunjungan = buat_kunjungan("F", _jam(HARI, 10))
    buat_triase(kunjungan, RiskLevel.RENDAH, waktu=_jam(HARI, 10, 1), jenis=JenisTriase.ULANG)
    assert RekapService().hitung(HARI, HARI).triase_ulang == 1


def test_validasi_gagal_untuk_rentang_terbalik():
    with pytest.raises(ValidasiGagalError):
        rentang_tanggal(date(2026, 3, 2), date(2026, 3, 1))
