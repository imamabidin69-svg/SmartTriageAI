"""Pencarian pasien dan registrasi kunjungan (FR-02, Desain 2.2)."""

import uuid
from datetime import date, timedelta

import pytest
from sqlalchemy import select

from app.models import Kunjungan, LogAudit, Pasien
from app.models.enums import AksiAudit, JenisKelamin, Peran, StatusKunjungan
from app.services import kunjungan_service
from app.utils.errors import Tipe
from app.utils.waktu import hari_ini, hitung_usia, usia_pasien

URL_KUNJUNGAN = "/api/v1/kunjungan"
URL_PASIEN = "/api/v1/pasien"
PASIEN_BARU = {"nama": "Budi Santoso", "perkiraan_usia": 45, "jenis_kelamin": "laki_laki"}


@pytest.fixture
def perawat(masuk):
    return masuk(Peran.PERAWAT)


def _pasien(sesi_db, pendaftar, **kolom):
    data = {"nama": "Pasien Lama", "perkiraan_usia": 50, "jenis_kelamin": JenisKelamin.PEREMPUAN, **kolom}
    pasien = Pasien(didaftarkan_oleh=pendaftar.id_pengguna, **data)
    sesi_db.add(pasien)
    sesi_db.commit()
    return pasien


# ---------------------------------------------------------------- registrasi


def test_registrasi_pasien_baru(client, perawat, sesi_db):
    pengguna, header = perawat
    respons = client.post(URL_KUNJUNGAN, json={**PASIEN_BARU, "nik": "3577010101800001"}, headers=header)

    assert respons.status_code == 201
    isi = respons.get_json()
    assert isi["pasien_baru"] is True
    assert isi["status"] == "menunggu"
    assert isi["waktu_datang"]
    pasien = sesi_db.get(Pasien, uuid.UUID(isi["id_pasien"]))
    assert (pasien.nama, pasien.nik, pasien.didaftarkan_oleh) == (
        "Budi Santoso",
        "3577010101800001",
        pengguna.id_pengguna,
    )
    kunjungan = sesi_db.get(Kunjungan, uuid.UUID(isi["id_kunjungan"]))
    assert kunjungan.status == StatusKunjungan.MENUNGGU

    [log] = sesi_db.scalars(select(LogAudit).where(LogAudit.aksi == AksiAudit.REGISTRASI_KUNJUNGAN)).all()
    assert log.id_aktor == pengguna.id_pengguna
    assert log.catatan == f"id_kunjungan={isi['id_kunjungan']}; id_pasien={isi['id_pasien']}; pasien_baru=ya"
    # Log audit tidak menyalin nama dan NIK pasien.
    assert "Budi" not in log.catatan
    assert "3577" not in log.catatan


def test_nama_dirapikan_dan_isian_kosong_dianggap_tidak_diisi(client, perawat, sesi_db):
    _, header = perawat
    isi = {**PASIEN_BARU, "nama": "  Budi   Santoso ", "nik": "", "no_telepon": " "}
    respons = client.post(URL_KUNJUNGAN, json=isi, headers=header)
    assert respons.status_code == 201
    pasien = sesi_db.get(Pasien, uuid.UUID(respons.get_json()["id_pasien"]))
    assert (pasien.nama, pasien.nik, pasien.no_telepon) == ("Budi Santoso", None, None)


def test_registrasi_dengan_tanggal_lahir_dan_telepon(client, perawat, sesi_db):
    _, header = perawat
    isi = {"nama": "Wulan", "tanggal_lahir": "1995-08-17", "jenis_kelamin": "perempuan", "no_telepon": "+62 812-3456"}
    respons = client.post(URL_KUNJUNGAN, json=isi, headers=header)
    assert respons.status_code == 201
    pasien = sesi_db.get(Pasien, uuid.UUID(respons.get_json()["id_pasien"]))
    assert (pasien.tanggal_lahir, pasien.perkiraan_usia, pasien.no_telepon) == (date(1995, 8, 17), None, "+62 812-3456")


def test_identitas_pasien_baru_wajib_lengkap(client, perawat):
    _, header = perawat
    respons = client.post(URL_KUNJUNGAN, json={}, headers=header)
    assert respons.status_code == 422
    assert respons.get_json()["errors"] == [
        {"field": "nama", "pesan": "Nama wajib diisi."},
        {"field": "jenis_kelamin", "pesan": "Jenis kelamin wajib diisi."},
        {"field": "tanggal_lahir", "pesan": "Isi tanggal lahir atau perkiraan usia."},
    ]


@pytest.mark.parametrize(
    ("ubah", "field", "pesan"),
    [
        ({"nik": "12345"}, "nik", "NIK harus 16 digit angka."),
        ({"nik": "35770101018000AB"}, "nik", "NIK harus 16 digit angka."),
        (
            {"no_telepon": "08x-123"},
            "no_telepon",
            "Nomor telepon hanya boleh berisi angka, spasi, tanda hubung, dan tanda + di depan.",
        ),
        ({"perkiraan_usia": 151}, "perkiraan_usia", "Perkiraan usia maksimal 150 tahun."),
        ({"jenis_kelamin": "pria"}, "jenis_kelamin", "Jenis kelamin harus salah satu dari: 'laki_laki', 'perempuan'."),
        ({"nama": "x" * 121}, "nama", "Nama maksimal 120 karakter."),
        (
            {"tanggal_lahir": "2000-13-01"},
            "tanggal_lahir",
            "Tanggal lahir harus berupa tanggal dengan format YYYY-MM-DD.",
        ),
        ({"alamat": "Jl. Mawar"}, "alamat", "Field alamat tidak dikenal."),
    ],
)
def test_validasi_isian_registrasi(client, perawat, ubah, field, pesan):
    _, header = perawat
    respons = client.post(URL_KUNJUNGAN, json={**PASIEN_BARU, **ubah}, headers=header)
    assert respons.status_code == 422
    assert respons.get_json()["errors"] == [{"field": field, "pesan": pesan}]


def test_tanggal_lahir_tidak_boleh_di_masa_depan(client, perawat):
    _, header = perawat
    besok = (hari_ini() + timedelta(days=1)).isoformat()
    respons = client.post(URL_KUNJUNGAN, json={**PASIEN_BARU, "tanggal_lahir": besok}, headers=header)
    assert respons.get_json()["errors"] == [
        {"field": "tanggal_lahir", "pesan": "Tanggal lahir tidak boleh melewati hari ini."}
    ]
    lama = date(hari_ini().year - 151, 1, 1).isoformat()
    respons = client.post(URL_KUNJUNGAN, json={**PASIEN_BARU, "tanggal_lahir": lama}, headers=header)
    assert respons.get_json()["errors"][0]["pesan"] == "Tanggal lahir terlalu jauh di masa lalu."


def test_memilih_pasien_lama_dengan_id(client, perawat, sesi_db):
    pengguna, header = perawat
    pasien = _pasien(sesi_db, pengguna)
    respons = client.post(URL_KUNJUNGAN, json={"id_pasien": str(pasien.id_pasien)}, headers=header)
    assert respons.status_code == 201
    assert respons.get_json()["pasien_baru"] is False
    assert respons.get_json()["id_pasien"] == str(pasien.id_pasien)
    log = sesi_db.scalar(select(LogAudit).where(LogAudit.aksi == AksiAudit.REGISTRASI_KUNJUNGAN))
    assert log.catatan.endswith("pasien_baru=tidak")


def test_id_pasien_yang_tidak_ada_ditolak(client, perawat):
    _, header = perawat
    respons = client.post(URL_KUNJUNGAN, json={"id_pasien": str(uuid.uuid4())}, headers=header)
    assert respons.status_code == 422
    assert respons.get_json()["errors"] == [{"field": "id_pasien", "pesan": "Pasien tidak ditemukan."}]


@pytest.mark.parametrize(
    "isian_lain",
    [
        {"nik": "3577010101800003"},
        {"nama": "", "jenis_kelamin": "pria", "tanggal_lahir": "2999-01-01", "no_telepon": "abc"},
        {"nama": "Nama Lain", "perkiraan_usia": 151},
    ],
)
def test_identitas_lain_diabaikan_bila_pasien_dipilih(client, perawat, sesi_db, isian_lain):
    """K8: form bisa masih membawa isian dari pencarian sebelumnya; yang dipakai hanya id_pasien."""
    pengguna, header = perawat
    pasien = _pasien(sesi_db, pengguna, nama="Pasien Lama", nik="3577010101800002")
    respons = client.post(URL_KUNJUNGAN, json={"id_pasien": str(pasien.id_pasien), **isian_lain}, headers=header)
    assert respons.status_code == 201
    sesi_db.refresh(pasien)
    assert (pasien.nama, pasien.nik, pasien.perkiraan_usia) == ("Pasien Lama", "3577010101800002", 50)


def test_field_tidak_dikenal_tetap_ditolak_walau_pasien_dipilih(client, perawat, sesi_db):
    pengguna, header = perawat
    pasien = _pasien(sesi_db, pengguna)
    respons = client.post(URL_KUNJUNGAN, json={"id_pasien": str(pasien.id_pasien), "alamat": "x"}, headers=header)
    assert respons.get_json()["errors"] == [{"field": "alamat", "pesan": "Field alamat tidak dikenal."}]


@pytest.mark.parametrize("nama", ["Bu\x00di", "\x1c", "Budi\x7f"])
def test_karakter_kontrol_di_nama_ditolak(client, perawat, nama):
    _, header = perawat
    respons = client.post(URL_KUNJUNGAN, json={**PASIEN_BARU, "nama": nama}, headers=header)
    assert respons.status_code == 422
    assert respons.get_json()["errors"] == [{"field": "nama", "pesan": "Nama berisi karakter yang tidak diizinkan."}]


def test_tab_di_nama_dirapikan_menjadi_spasi(client, perawat, sesi_db):
    _, header = perawat
    respons = client.post(URL_KUNJUNGAN, json={**PASIEN_BARU, "nama": "Budi\tSantoso"}, headers=header)
    pasien = sesi_db.get(Pasien, uuid.UUID(respons.get_json()["id_pasien"]))
    assert pasien.nama == "Budi Santoso"


def test_nik_terdaftar_dengan_identitas_sama_memakai_pasien_lama(client, perawat, sesi_db):
    pengguna, header = perawat
    pasien = _pasien(sesi_db, pengguna, nama="Siti Rahma", nik="3577010101800004")
    isi = {"nama": "  siti  RAHMA", "jenis_kelamin": "perempuan", "perkiraan_usia": 51, "nik": "3577010101800004"}
    respons = client.post(URL_KUNJUNGAN, json=isi, headers=header)
    assert respons.status_code == 201
    assert respons.get_json()["pasien_baru"] is False
    assert respons.get_json()["id_pasien"] == str(pasien.id_pasien)


@pytest.mark.parametrize(
    "isi",
    [
        {"nama": "Orang Lain", "jenis_kelamin": "perempuan", "perkiraan_usia": 30},
        {"nama": "Siti Rahma", "jenis_kelamin": "laki_laki", "perkiraan_usia": 30},
    ],
)
def test_nik_terdaftar_atas_pasien_lain_dibalas_409(client, perawat, sesi_db, isi):
    pengguna, header = perawat
    _pasien(sesi_db, pengguna, nama="Siti Rahma", nik="3577010101800005")
    respons = client.post(URL_KUNJUNGAN, json={**isi, "nik": "3577010101800005"}, headers=header)
    assert respons.status_code == 409
    assert respons.get_json()["type"] == Tipe.KONFLIK
    assert "NIK sudah terdaftar" in respons.get_json()["detail"]


@pytest.mark.parametrize("status", [StatusKunjungan.MENUNGGU, StatusKunjungan.DITANGANI])
def test_pasien_dengan_kunjungan_aktif_tidak_didaftarkan_lagi(client, perawat, sesi_db, status):
    pengguna, header = perawat
    pasien = _pasien(sesi_db, pengguna)
    aktif = Kunjungan(id_pasien=pasien.id_pasien, status=status)
    sesi_db.add(aktif)
    sesi_db.commit()

    respons = client.post(URL_KUNJUNGAN, json={"id_pasien": str(pasien.id_pasien)}, headers=header)
    assert respons.status_code == 409
    assert respons.get_json()["id_kunjungan_aktif"] == str(aktif.id_kunjungan)
    assert sesi_db.scalars(select(LogAudit)).all() == []


def test_pasien_yang_kunjungannya_selesai_boleh_datang_lagi(client, perawat, sesi_db):
    pengguna, header = perawat
    pasien = _pasien(sesi_db, pengguna)
    sesi_db.add(Kunjungan(id_pasien=pasien.id_pasien, status=StatusKunjungan.SELESAI))
    sesi_db.commit()
    respons = client.post(URL_KUNJUNGAN, json={"id_pasien": str(pasien.id_pasien)}, headers=header)
    assert respons.status_code == 201


def test_nik_bentrok_saat_disimpan_dibalas_409(client, perawat, sesi_db, monkeypatch):
    """Meniru dua registrasi bersamaan: pencarian NIK belum melihat pasien yang baru disimpan request lain."""
    pengguna, header = perawat
    _pasien(sesi_db, pengguna, nama="Budi Santoso", nik="3577010101800006")
    monkeypatch.setattr(kunjungan_service.KunjunganService, "_pasien_dengan_nik", staticmethod(lambda _nik: None))
    respons = client.post(URL_KUNJUNGAN, json={**PASIEN_BARU, "nik": "3577010101800006"}, headers=header)
    assert respons.status_code == 409
    assert "baru saja didaftarkan" in respons.get_json()["detail"]
    assert sesi_db.scalars(select(Kunjungan)).all() == []


@pytest.mark.parametrize("peran", [Peran.DOKTER, Peran.ADMIN])
def test_registrasi_hanya_untuk_perawat(client, masuk, peran):
    _, header = masuk(peran)
    assert client.post(URL_KUNJUNGAN, json=PASIEN_BARU, headers=header).status_code == 403


# ---------------------------------------------------------------- pencarian


def test_cari_pasien_berdasarkan_potongan_nama(client, perawat, sesi_db):
    pengguna, header = perawat
    lahir = date(1990, 5, 17)
    budi = _pasien(sesi_db, pengguna, nama="Budi Hartono", nik="3577010101900001", tanggal_lahir=lahir)
    _pasien(sesi_db, pengguna, nama="Andi Wijaya")
    aktif = Kunjungan(id_pasien=budi.id_pasien)
    sesi_db.add(aktif)
    sesi_db.commit()

    respons = client.get(URL_PASIEN, query_string={"q": " budi "}, headers=header)
    assert respons.status_code == 200
    assert respons.get_json() == {
        "items": [
            {
                "id_pasien": str(budi.id_pasien),
                "nama": "Budi Hartono",
                "jenis_kelamin": "perempuan",
                "tanggal_lahir": "1990-05-17",
                "perkiraan_usia": 50,
                "usia": hitung_usia(lahir, hari_ini()),
                "nik_tersamar": "************0001",
                "id_kunjungan_aktif": str(aktif.id_kunjungan),
            }
        ]
    }


def test_cari_pasien_dengan_nik_lengkap(client, perawat, sesi_db):
    pengguna, header = perawat
    pasien = _pasien(sesi_db, pengguna, nama="Rina", nik="3577010101900002")
    _pasien(sesi_db, pengguna, nama="3577010101900002 bukan nik")
    respons = client.get(URL_PASIEN, query_string={"q": "3577010101900002"}, headers=header)
    assert [p["id_pasien"] for p in respons.get_json()["items"]] == [str(pasien.id_pasien)]
    assert respons.get_json()["items"][0]["id_kunjungan_aktif"] is None


def test_tanda_persen_di_pencarian_tidak_dianggap_wildcard(client, perawat, sesi_db):
    pengguna, header = perawat
    _pasien(sesi_db, pengguna, nama="Ahmad")
    respons = client.get(URL_PASIEN, query_string={"q": "%%"}, headers=header)
    assert respons.get_json() == {"items": []}


def test_hasil_pencarian_dibatasi_dan_diurutkan_nama(client, perawat, sesi_db):
    pengguna, header = perawat
    # Disisipkan terbalik supaya urutan simpan berbeda dari urutan nama.
    semua = [f"Pasien Uji {i:02d}" for i in range(25)]
    for nama in reversed(semua):
        _pasien(sesi_db, pengguna, nama=nama)
    items = client.get(URL_PASIEN, query_string={"q": "uji"}, headers=header).get_json()["items"]
    assert [p["nama"] for p in items] == sorted(semua)[:20]


def test_garis_bawah_di_pencarian_tidak_dianggap_wildcard(client, perawat, sesi_db):
    pengguna, header = perawat
    _pasien(sesi_db, pengguna, nama="Ahmad")
    assert client.get(URL_PASIEN, query_string={"q": "__"}, headers=header).get_json() == {"items": []}


def test_karakter_kontrol_di_pencarian_ditolak(client, perawat):
    _, header = perawat
    respons = client.get(URL_PASIEN, query_string={"q": "bu\x00di"}, headers=header)
    assert respons.status_code == 422
    assert respons.get_json()["errors"] == [
        {"field": "q", "pesan": "Kata kunci pencarian berisi karakter yang tidak diizinkan."}
    ]


@pytest.mark.parametrize("q", ["", "a", " b "])
def test_kata_kunci_minimal_dua_karakter(client, perawat, q):
    _, header = perawat
    respons = client.get(URL_PASIEN, query_string={"q": q}, headers=header)
    assert respons.status_code == 422
    assert respons.get_json()["errors"][0]["field"] == "q"


def test_kata_kunci_wajib(client, perawat):
    _, header = perawat
    respons = client.get(URL_PASIEN, headers=header)
    assert respons.get_json()["errors"] == [{"field": "q", "pesan": "Kata kunci pencarian wajib diisi."}]


@pytest.mark.parametrize(("peran", "status"), [(Peran.DOKTER, 200), (Peran.ADMIN, 403)])
def test_peran_pencarian(client, masuk, peran, status):
    _, header = masuk(peran)
    assert client.get(URL_PASIEN, query_string={"q": "budi"}, headers=header).status_code == status


# ---------------------------------------------------------------- usia


@pytest.mark.parametrize(
    ("lahir", "pada", "usia"),
    [
        (date(2000, 3, 15), date(2026, 3, 14), 25),
        (date(2000, 3, 15), date(2026, 3, 15), 26),
        (date(2000, 2, 29), date(2026, 2, 28), 25),
    ],
)
def test_hitung_usia(lahir, pada, usia):
    assert hitung_usia(lahir, pada) == usia


def test_usia_pasien_memakai_perkiraan_bila_tanggal_lahir_kosong():
    assert usia_pasien(None, 40) == 40
    assert usia_pasien(None, None) is None
    assert usia_pasien(date(2000, 1, 1), 99, pada=date(2010, 1, 1)) == 10


# ---------------------------------------------------------------- batas pencarian NIK (keputusan NIK pilihan b)

NIK_TIDAK_ADA = "3577019999990001"


@pytest.fixture
def batas_kecil(app, monkeypatch):
    monkeypatch.setitem(app.config, "BATAS_CARI_NIK", "3 per 15 minutes")


def _cari(client, header, q):
    return client.get(URL_PASIEN, query_string={"q": q}, headers=header)


def test_batas_bawaan_cari_nik():
    from app.config import Config

    assert Config.BATAS_CARI_NIK == "30 per 15 minutes"


def test_pencarian_nik_gagal_dibatasi_per_akun(client, perawat, batas_kecil):
    _, header = perawat
    assert [_cari(client, header, NIK_TIDAK_ADA).status_code for _ in range(3)] == [200, 200, 200]

    respons = _cari(client, header, NIK_TIDAK_ADA)
    assert respons.status_code == 429
    assert respons.content_type == "application/problem+json"
    assert respons.get_json()["type"] == Tipe.TERLALU_BANYAK_PERCOBAAN
    assert respons.get_json()["detail"] == (
        "Terlalu banyak pencarian NIK yang tidak ditemukan. Coba lagi beberapa saat lagi, atau cari dengan nama."
    )
    assert 840 <= int(respons.headers["Retry-After"]) <= 900


def test_setelah_dibatasi_nik_yang_ada_pun_ditolak_tetapi_nama_tetap_bisa(client, perawat, sesi_db, batas_kecil):
    pengguna, header = perawat
    _pasien(sesi_db, pengguna, nama="Rina", nik="3577010101900002")
    for _ in range(3):
        _cari(client, header, NIK_TIDAK_ADA)
    assert _cari(client, header, "3577010101900002").status_code == 429
    assert _cari(client, header, "Rina").status_code == 200


def test_pencarian_nik_yang_ditemukan_dan_pencarian_nama_tidak_dihitung(client, perawat, sesi_db, batas_kecil):
    pengguna, header = perawat
    _pasien(sesi_db, pengguna, nama="Rina", nik="3577010101900002")
    for _ in range(5):
        assert _cari(client, header, "3577010101900002").status_code == 200
        assert _cari(client, header, "Tidak Ada Nama Ini").status_code == 200
    assert _cari(client, header, NIK_TIDAK_ADA).status_code == 200


def test_batas_nik_dihitung_terpisah_per_akun(client, masuk, batas_kecil):
    _, header_a = masuk(Peran.PERAWAT)
    _, header_b = masuk(Peran.DOKTER)
    for _ in range(3):
        _cari(client, header_a, NIK_TIDAK_ADA)
    assert _cari(client, header_a, NIK_TIDAK_ADA).status_code == 429
    assert _cari(client, header_b, NIK_TIDAK_ADA).status_code == 200


def test_batas_nik_tidak_berlaku_bila_limiter_dimatikan(client, perawat, batas_kecil, monkeypatch):
    from app.extensions import limiter

    monkeypatch.setattr(limiter, "enabled", False)
    _, header = perawat
    assert [_cari(client, header, NIK_TIDAK_ADA).status_code for _ in range(5)] == [200] * 5
