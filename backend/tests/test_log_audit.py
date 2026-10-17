"""GET /admin/log-audit dengan filter dan kursor (FR-09, NFR-06, keputusan K13)."""

import uuid
from datetime import date, datetime, time, timedelta

import pytest

from app.models import LogAudit
from app.models.enums import AksiAudit, Peran, RiskLevel
from app.utils.waktu import WIB

URL = "/api/v1/admin/log-audit"
HARI = date(2026, 3, 10)


@pytest.fixture
def admin(masuk):
    return masuk(Peran.ADMIN)


@pytest.fixture
def buat_log(sesi_db):
    def _buat(aktor, aksi=AksiAudit.UBAH_KONFIGURASI, waktu=None, **kolom):
        log = LogAudit(id_aktor=aktor.id_pengguna, aksi=aksi, **kolom)
        if waktu is not None:
            log.waktu = waktu
        sesi_db.add(log)
        sesi_db.commit()
        return log

    return _buat


def _jam(hari, jam):
    return datetime.combine(hari, time(jam), WIB)


def test_log_audit_terbaru_lebih_dulu_dengan_nama_aktor(client, admin, buat_log, buat_pengguna, kunjungan, buat_triase):
    pengguna_admin, header = admin
    dokter = buat_pengguna(Peran.DOKTER)
    triase = buat_triase(kunjungan, RiskLevel.SEDANG)
    lama = buat_log(pengguna_admin, waktu=_jam(HARI, 8), catatan="ambang_kritis: 6 -> 7")
    baru = buat_log(
        dokter,
        AksiAudit.KOREKSI,
        _jam(HARI, 9),
        id_triase=triase.id_triase,
        level_sebelum=RiskLevel.SEDANG,
        level_sesudah=RiskLevel.TINGGI,
        catatan="Nyeri dada khas",
    )

    isi = client.get(URL, headers=header).get_json()
    assert [i["id_log"] for i in isi["items"]] == [str(baru.id_log), str(lama.id_log)]
    item = isi["items"][0]
    assert item["aksi"] == "koreksi"
    assert item["aktor"] == {"id_pengguna": str(dokter.id_pengguna), "nama": dokter.nama}
    assert (item["id_triase"], item["level_sebelum"], item["level_sesudah"], item["catatan"]) == (
        str(triase.id_triase),
        "sedang",
        "tinggi",
        "Nyeri dada khas",
    )
    assert isi["kursor_berikutnya"] is None


def test_filter_log_audit(client, admin, buat_log, buat_pengguna):
    pengguna_admin, header = admin
    dokter = buat_pengguna(Peran.DOKTER)
    kemarin = buat_log(pengguna_admin, waktu=_jam(HARI - timedelta(days=1), 23))
    hari_ini = buat_log(pengguna_admin, AksiAudit.TAMBAH_STAF, _jam(HARI, 0))
    oleh_dokter = buat_log(dokter, AksiAudit.SETUJUI, _jam(HARI, 12))
    besok = buat_log(pengguna_admin, waktu=_jam(HARI + timedelta(days=1), 0))

    def ambil(**query):
        return [i["id_log"] for i in client.get(URL, query_string=query, headers=header).get_json()["items"]]

    assert ambil(dari=HARI.isoformat(), sampai=HARI.isoformat()) == [str(oleh_dokter.id_log), str(hari_ini.id_log)]
    assert ambil(dari=HARI.isoformat()) == [str(besok.id_log), str(oleh_dokter.id_log), str(hari_ini.id_log)]
    assert ambil(sampai=(HARI - timedelta(days=1)).isoformat()) == [str(kemarin.id_log)]
    assert ambil(aksi="tambah_staf") == [str(hari_ini.id_log)]
    assert ambil(id_aktor=str(dokter.id_pengguna)) == [str(oleh_dokter.id_log)]
    assert ambil(id_triase=str(uuid.uuid4())) == []


def test_paginasi_log_audit(client, admin, buat_log):
    pengguna_admin, header = admin
    log = [buat_log(pengguna_admin, waktu=_jam(HARI, 1) + timedelta(minutes=m)) for m in range(5)]
    terbaca, kursor = [], None
    while True:
        query = {"ukuran": 2, **({"kursor": kursor} if kursor else {})}
        isi = client.get(URL, query_string=query, headers=header).get_json()
        terbaca += [i["id_log"] for i in isi["items"]]
        kursor = isi["kursor_berikutnya"]
        if kursor is None:
            break
    assert terbaca == [str(entri.id_log) for entri in reversed(log)]


@pytest.mark.parametrize(
    ("query", "field", "pesan"),
    [
        ({"dari": "2026-03-10", "sampai": "2026-03-09"}, "dari", "Tanggal awal tidak boleh melewati tanggal akhir."),
        ({"aksi": "hapus"}, "aksi", None),
        ({"ukuran": 51}, "ukuran", "Ukuran halaman maksimal 50."),
        ({"kursor": "xyz"}, "kursor", "Kursor tidak valid. Muat ulang dari halaman pertama."),
        ({"id_aktor": "bukan-uuid"}, "id_aktor", "ID aktor harus berupa UUID yang valid."),
    ],
)
def test_parameter_log_audit_tidak_valid(client, admin, query, field, pesan):
    _, header = admin
    respons = client.get(URL, query_string=query, headers=header)
    assert respons.status_code == 422
    [galat] = respons.get_json()["errors"]
    assert galat["field"] == field
    if pesan:
        assert galat["pesan"] == pesan


@pytest.mark.parametrize("peran", [Peran.PERAWAT, Peran.DOKTER])
def test_log_audit_hanya_untuk_admin(client, masuk, peran):
    _, header = masuk(peran)
    assert client.get(URL, headers=header).status_code == 403
