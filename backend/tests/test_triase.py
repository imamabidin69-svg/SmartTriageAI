"""Observasi ICU: POST /kunjungan/{id}/triase dan GET /triase/{id} (FR-03, FR-05, SKPL TC-05 sampai TC-09)."""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from bantuan import header_masuk
from conftest import PENJELASAN_KOSONG
from sqlalchemy import update

from app.ai import klasifikasi
from app.ai.registry import ModelPerburukan
from app.models import Konfigurasi, Kunjungan, LogAudit, Pasien, PemindaianAlat, Triase
from app.models.enums import (
    AksiAudit,
    JenisAlat,
    JenisKelamin,
    Peran,
    RiskLevel,
    StatusKunjungan,
    StatusValidasi,
)
from app.services.triase_service import PeringatanVital, TriaseService
from app.utils.errors import Tipe
from app.utils.schemas import TandaVital
from app.utils.waktu import hari_ini, sekarang

TANDA_VITAL_NORMAL = {
    "td_sistolik": 120,
    "td_diastolik": 80,
    "nadi": 82,
    "laju_napas": 18,
    "suhu": 36.8,
    "saturasi": 98,
}
ISIAN = {
    "tingkat_kesadaran": "A",
    "oksigen_tambahan": False,
    "tanda_vital": TANDA_VITAL_NORMAL,
}
# Pasien syok: NEWS2 napas 3, saturasi 3, oksigen 2, sistolik 3, nadi 2, kesadaran 3, suhu 1 = 17.
TANDA_VITAL_SYOK = {"td_sistolik": 86, "td_diastolik": 48, "nadi": 128, "laju_napas": 27, "suhu": 38.9, "saturasi": 90}


def _url(kunjungan) -> str:
    return f"/api/v1/kunjungan/{kunjungan.id_kunjungan}/triase"


def _isian(**ubah):
    tanda_vital = {**TANDA_VITAL_NORMAL, **ubah.pop("tanda_vital", {})}
    return {**ISIAN, **ubah, "tanda_vital": tanda_vital}


@pytest.fixture
def perawat(masuk):
    return masuk(Peran.PERAWAT)


def test_input_triase_menyimpan_rekomendasi_model(client, perawat, kunjungan, sesi_db):
    pengguna, header = perawat
    respons = client.post(_url(kunjungan), json=_isian(), headers=header)

    assert respons.status_code == 201
    isi = respons.get_json()
    assert isi["jenis"] == "awal"
    assert isi["status_validasi"] == "menunggu"
    assert isi["sumber_rekomendasi"] == "model"
    assert isi["sumber_tanda_vital"] == "manual"
    assert isi["risk_level"] in {"rendah", "sedang", "tinggi", "kritis"}
    assert isi["dibuat_oleh"] == {"id_pengguna": str(pengguna.id_pengguna), "nama": pengguna.nama}
    assert isi["divalidasi_oleh"] is None
    assert isi["pasien"] == {
        "id_pasien": str(kunjungan.id_pasien),
        "nama": "Pasien Simulasi",
        "usia": 40,
        "jenis_kelamin": "perempuan",
    }
    assert isi["tanda_vital"] == {**TANDA_VITAL_NORMAL, "saturasi": 98.0}
    assert isi["lab"] == {"laktat": None, "kreatinin": None, "trombosit": None, "leukosit": None, "bilirubin": None}
    assert (isi["oksigen_tambahan"], isi["ventilator"], isi["vasopresor"], isi["catatan"]) == (
        False,
        False,
        False,
        None,
    )
    assert isi["nomor_bed"] is None
    assert isi["status_kunjungan"] == "menunggu"
    assert isi["level_sebelumnya"] is None
    assert isi["peringatan"] == []
    assert isi["catatan_validasi_terakhir"] is None
    assert isi["skor_news2"] == 0
    assert 0 <= isi["peluang_perburukan"] <= 1
    penjelasan = isi["penjelasan_ai"]
    assert penjelasan["versi_model"] == "rf-icu-physionet2019-v1"
    assert (penjelasan["skor_news2"], penjelasan["level_news2"], penjelasan["komponen_news2"]) == (0, "rendah", [])
    assert penjelasan["peluang_perburukan"] == isi["peluang_perburukan"]
    assert penjelasan["level_model"] in {"rendah", "sedang", "tinggi", "kritis"}
    assert len(penjelasan["faktor"]) == 3
    # Hasil lab yang tidak diisi tidak boleh muncul sebagai faktor penjelas.
    assert {f["fitur"] for f in penjelasan["faktor"]}.isdisjoint({"laktat", "kreatinin", "trombosit"})

    triase = sesi_db.get(Triase, uuid.UUID(isi["id_triase"]))
    assert triase.penjelasan_ai == penjelasan
    assert triase.skor_news2 == 0
    # Membuat triase tidak menulis log audit; yang diaudit adalah validasinya (Desain Gambar 2.9).
    assert sesi_db.query(LogAudit).count() == 0


def test_observasi_kedua_dicatat_sebagai_observasi_ulang(client, perawat, kunjungan):
    _, header = perawat
    pertama = client.post(_url(kunjungan), json=_isian(), headers=header).get_json()
    kedua = client.post(_url(kunjungan), json=_isian(), headers=header).get_json()
    assert (pertama["jenis"], kedua["jenis"]) == ("awal", "ulang")
    assert kedua["level_sebelumnya"] == pertama["risk_level"]


def test_pasien_syok_kritis_dan_news2_dijelaskan(client, perawat, kunjungan):
    _, header = perawat
    isian = _isian(tingkat_kesadaran="V", oksigen_tambahan=True, tanda_vital=TANDA_VITAL_SYOK)
    isi = client.post(_url(kunjungan), json=isian, headers=header).get_json()
    assert isi["risk_level"] == "kritis"
    assert isi["skor_news2"] == 17
    komponen = isi["penjelasan_ai"]["komponen_news2"]
    assert [k["kontribusi"] for k in komponen] == [3, 3, 3, 3, 2, 2, 1]
    assert {k["fitur"] for k in komponen} == {
        "laju_napas",
        "saturasi",
        "oksigen_tambahan",
        "td_sistolik",
        "nadi",
        "tingkat_kesadaran",
        "suhu",
    }


def test_level_akhir_tidak_pernah_lebih_rendah_dari_news2(client, perawat, kunjungan, monkeypatch):
    """Walau model menilai rendah, level NEWS2 yang lebih tinggi tetap dipakai."""
    monkeypatch.setattr(ModelPerburukan, "level", lambda self, peluang: RiskLevel.RENDAH)
    _, header = perawat
    isian = _isian(tingkat_kesadaran="V", oksigen_tambahan=True, tanda_vital=TANDA_VITAL_SYOK)
    isi = client.post(_url(kunjungan), json=isian, headers=header).get_json()
    assert isi["penjelasan_ai"]["level_model"] == "rendah"
    assert isi["risk_level"] == "kritis"
    assert isi["sumber_rekomendasi"] == "model"


def test_level_model_dipakai_bila_lebih_tinggi_dari_news2(client, perawat, kunjungan, monkeypatch):
    monkeypatch.setattr(ModelPerburukan, "level", lambda self, peluang: RiskLevel.TINGGI)
    _, header = perawat
    isi = client.post(_url(kunjungan), json=_isian(), headers=header).get_json()
    assert isi["penjelasan_ai"]["level_news2"] == "rendah"
    assert isi["risk_level"] == "tinggi"


def test_hasil_lab_dan_alat_bantu_disimpan(client, perawat, kunjungan, sesi_db):
    _, header = perawat
    lab = {"laktat": 4.25, "kreatinin": "2.104", "trombosit": 95, "leukosit": 19.84, "bilirubin": 1.8}
    isian = _isian(lab=lab, ventilator=True, vasopresor=True, oksigen_tambahan=True, catatan="  Urin 20 ml/jam  ")
    isi = client.post(_url(kunjungan), json=isian, headers=header).get_json()
    assert isi["lab"] == {"laktat": 4.3, "kreatinin": 2.1, "trombosit": 95, "leukosit": 19.8, "bilirubin": 1.8}
    assert (isi["ventilator"], isi["vasopresor"], isi["catatan"]) == (True, True, "Urin 20 ml/jam")
    triase = sesi_db.get(Triase, uuid.UUID(isi["id_triase"]))
    assert (triase.laktat, triase.kreatinin, triase.trombosit) == (Decimal("4.3"), Decimal("2.10"), 95)


# ---------------------------------------------------------------- persetujuan dokter hanya saat level naik


def _observasi(client, header, kunjungan, syok=False):
    syok_isian = {"tingkat_kesadaran": "V", "oksigen_tambahan": True, "tanda_vital": TANDA_VITAL_SYOK}
    isian = _isian(**syok_isian) if syok else _isian()
    return client.post(_url(kunjungan), json=isian, headers=header).get_json()


def _setujui(client, header, id_triase):
    respons = client.post(f"/api/v1/triase/{id_triase}/validasi", json={"aksi": "setujui"}, headers=header)
    assert respons.status_code == 200


@pytest.fixture
def model_ikut_news2(monkeypatch):
    """Model dibuat selalu rendah supaya level akhir hanya mengikuti NEWS2 dan mudah diatur di tes."""
    monkeypatch.setattr(ModelPerburukan, "level", lambda self, peluang: RiskLevel.RENDAH)


@pytest.mark.usefixtures("model_ikut_news2")
def test_penilaian_awal_menunggu_persetujuan_dokter(client, perawat, kunjungan):
    _, header = perawat
    assert _observasi(client, header, kunjungan)["status_validasi"] == "menunggu"


@pytest.mark.usefixtures("model_ikut_news2")
def test_observasi_dengan_level_sama_langsung_tercatat(client, perawat, masuk, kunjungan):
    _, header = perawat
    _, header_dokter = masuk(Peran.DOKTER)
    _setujui(client, header_dokter, _observasi(client, header, kunjungan)["id_triase"])
    ulang = _observasi(client, header, kunjungan)
    assert (ulang["risk_level"], ulang["status_validasi"]) == ("rendah", "tercatat")


@pytest.mark.usefixtures("model_ikut_news2")
def test_level_naik_menunggu_persetujuan_lalu_turun_tercatat(client, perawat, masuk, kunjungan):
    _, header = perawat
    _, header_dokter = masuk(Peran.DOKTER)
    _setujui(client, header_dokter, _observasi(client, header, kunjungan)["id_triase"])

    naik = _observasi(client, header, kunjungan, syok=True)
    assert (naik["risk_level"], naik["status_validasi"], naik["level_sebelumnya"]) == ("kritis", "menunggu", "rendah")
    _setujui(client, header_dokter, naik["id_triase"])

    turun = _observasi(client, header, kunjungan)
    assert (turun["risk_level"], turun["status_validasi"]) == ("rendah", "tercatat")


@pytest.mark.usefixtures("model_ikut_news2")
def test_kenaikan_yang_belum_disetujui_tidak_hilang(client, perawat, masuk, kunjungan):
    """Acuannya level final terakhir: kenaikan tetap menunggu dokter walau ada observasi baru setelahnya."""
    _, header = perawat
    _, header_dokter = masuk(Peran.DOKTER)
    _setujui(client, header_dokter, _observasi(client, header, kunjungan)["id_triase"])
    _observasi(client, header, kunjungan, syok=True)
    lagi = _observasi(client, header, kunjungan, syok=True)
    assert (lagi["status_validasi"], lagi["level_sebelumnya"]) == ("menunggu", "kritis")


def test_status_awal_tanpa_acuan_menunggu():
    assert TriaseService.status_awal(RiskLevel.RENDAH, None) == StatusValidasi.MENUNGGU


def test_suhu_dan_saturasi_dibulatkan_satu_desimal(client, perawat, kunjungan, sesi_db):
    _, header = perawat
    isian = _isian(tanda_vital={"suhu": 37.25, "saturasi": "97.04"})
    isi = client.post(_url(kunjungan), json=isian, headers=header).get_json()
    assert isi["tanda_vital"]["suhu"] == 37.3
    assert isi["tanda_vital"]["saturasi"] == 97.0
    triase = sesi_db.get(Triase, uuid.UUID(isi["id_triase"]))
    assert triase.suhu == Decimal("37.3")


# ---------------------------------------------------------------- validasi isian


@pytest.mark.parametrize(
    ("ubah", "errors"),
    [
        (
            {"tanda_vital": {"saturasi": 120}},
            [{"field": "tanda_vital.saturasi", "pesan": "Saturasi oksigen maksimal 100%."}],
        ),
        (
            {"tanda_vital": {"td_sistolik": 400, "suhu": 10}},
            [
                {"field": "tanda_vital.td_sistolik", "pesan": "Tekanan darah sistolik maksimal 320 mmHg."},
                {"field": "tanda_vital.suhu", "pesan": "Suhu tubuh minimal 20°C."},
            ],
        ),
        (
            {"tanda_vital": {"nadi": 80.5}},
            [{"field": "tanda_vital.nadi", "pesan": "Nadi harus berupa bilangan bulat."}],
        ),
        ({"lab": {"laktat": 31}}, [{"field": "lab.laktat", "pesan": "Laktat maksimal 30 mmol/L."}]),
        ({"lab": {"kreatinin": -1}}, [{"field": "lab.kreatinin", "pesan": "Kreatinin minimal 0 mg/dL."}]),
        ({"lab": {"trombosit": 2001}}, [{"field": "lab.trombosit", "pesan": "Trombosit maksimal 2000 ribu/µL."}]),
        ({"lab": {"leukosit": 301}}, [{"field": "lab.leukosit", "pesan": "Leukosit maksimal 300 ribu/µL."}]),
        ({"lab": {"bilirubin": 61}}, [{"field": "lab.bilirubin", "pesan": "Bilirubin maksimal 60 mg/dL."}]),
        ({"catatan": "x" * 501}, [{"field": "catatan", "pesan": "Catatan maksimal 500 karakter."}]),
        (
            {"tingkat_kesadaran": "X"},
            [{"field": "tingkat_kesadaran", "pesan": "Tingkat kesadaran harus salah satu dari: 'A', 'V', 'P', 'U'."}],
        ),
        (
            {"id_pemindaian": ["bukan-uuid"]},
            [{"field": "id_pemindaian.0", "pesan": "ID pemindaian harus berupa UUID yang valid."}],
        ),
    ],
)
def test_nilai_yang_tidak_mungkin_ditolak_per_field(client, perawat, kunjungan, ubah, errors):
    _, header = perawat
    respons = client.post(_url(kunjungan), json=_isian(**ubah), headers=header)
    assert respons.status_code == 422
    assert respons.get_json()["errors"] == errors


@pytest.mark.parametrize("field", ["oksigen_tambahan", "tingkat_kesadaran", "tanda_vital"])
def test_isian_wajib(client, perawat, kunjungan, field):
    _, header = perawat
    isian = _isian()
    del isian[field]
    respons = client.post(_url(kunjungan), json=isian, headers=header)
    assert respons.status_code == 422
    assert respons.get_json()["errors"][0]["field"] == field
    assert respons.get_json()["errors"][0]["pesan"].endswith("wajib diisi.")


def test_field_lama_igd_ditolak(client, perawat, kunjungan):
    _, header = perawat
    respons = client.post(_url(kunjungan), json=_isian(kategori_keluhan="Pusing"), headers=header)
    assert respons.status_code == 422
    assert respons.get_json()["errors"][0]["field"] == "kategori_keluhan"


def test_kunjungan_tidak_ditemukan(client, perawat):
    _, header = perawat
    respons = client.post(f"/api/v1/kunjungan/{uuid.uuid4()}/triase", json=_isian(), headers=header)
    assert respons.status_code == 404
    assert respons.get_json()["type"] == Tipe.TIDAK_DITEMUKAN


def test_id_kunjungan_bukan_uuid_dibalas_404(client, perawat):
    _, header = perawat
    assert client.post("/api/v1/kunjungan/123/triase", json=_isian(), headers=header).status_code == 404


def _ubah_status(sesi_db, kunjungan, status):
    sesi_db.execute(update(Kunjungan).where(Kunjungan.id_kunjungan == kunjungan.id_kunjungan).values(status=status))
    sesi_db.commit()


def test_pasien_yang_keluar_icu_tidak_bisa_diobservasi(client, perawat, kunjungan, sesi_db):
    _, header = perawat
    _ubah_status(sesi_db, kunjungan, StatusKunjungan.SELESAI)
    respons = client.post(_url(kunjungan), json=_isian(), headers=header)
    assert respons.status_code == 409
    assert respons.get_json()["type"] == Tipe.KONFLIK
    assert "keluar dari ICU" in respons.get_json()["detail"]


def test_pasien_yang_sedang_tindakan_tetap_bisa_diobservasi(client, perawat, kunjungan, sesi_db):
    _, header = perawat
    _ubah_status(sesi_db, kunjungan, StatusKunjungan.DITANGANI)
    assert client.post(_url(kunjungan), json=_isian(), headers=header).status_code == 201


@pytest.mark.parametrize("peran", [Peran.DOKTER, Peran.ADMIN])
def test_input_triase_hanya_untuk_perawat(client, masuk, kunjungan, peran):
    _, header = masuk(peran)
    assert client.post(_url(kunjungan), json=_isian(), headers=header).status_code == 403


# ---------------------------------------------------------------- peringatan nilai tidak wajar


def test_nilai_tidak_wajar_tetap_diterima_dengan_peringatan(client, perawat, kunjungan):
    _, header = perawat
    isian = _isian(tanda_vital={"saturasi": 85, "td_sistolik": 300})
    respons = client.post(_url(kunjungan), json=isian, headers=header)
    assert respons.status_code == 201
    assert respons.get_json()["peringatan"] == [
        {
            "field": "tanda_vital.td_sistolik",
            "pesan": "Tekanan darah sistolik 300 mmHg tidak lazim. Pastikan tidak salah ketik.",
        },
        {"field": "tanda_vital.saturasi", "pesan": "Saturasi oksigen 85% di bawah batas wajar (< 90%)."},
    ]


@pytest.mark.parametrize(
    ("ubah", "pesan"),
    [
        ({"td_sistolik": 89}, "Tekanan darah sistolik 89 mmHg di bawah batas wajar (< 90 mmHg)."),
        ({"td_sistolik": 180}, "Tekanan darah sistolik 180 mmHg melewati batas wajar (≥ 180 mmHg)."),
        (
            {"td_sistolik": 160, "td_diastolik": 125},
            "Tekanan darah diastolik 125 mmHg melewati batas wajar (≥ 120 mmHg).",
        ),
        ({"td_diastolik": 15}, "Tekanan darah diastolik 15 mmHg tidak lazim. Pastikan tidak salah ketik."),
        ({"nadi": 49}, "Nadi 49 x/menit di bawah batas wajar (< 50 x/menit)."),
        ({"nadi": 130}, "Nadi 130 x/menit melewati batas wajar (≥ 130 x/menit)."),
        ({"nadi": 251}, "Nadi 251 x/menit tidak lazim. Pastikan tidak salah ketik."),
        ({"laju_napas": 9}, "Laju napas 9 x/menit di bawah batas wajar (< 10 x/menit)."),
        ({"laju_napas": 30}, "Laju napas 30 x/menit melewati batas wajar (≥ 30 x/menit)."),
        ({"laju_napas": 4}, "Laju napas 4 x/menit tidak lazim. Pastikan tidak salah ketik."),
        ({"suhu": Decimal("34.9")}, "Suhu tubuh 34,9 °C di bawah batas wajar (< 35 °C)."),
        ({"suhu": Decimal("39.0")}, "Suhu tubuh 39 °C melewati batas wajar (≥ 39 °C)."),
        ({"suhu": Decimal("43.5")}, "Suhu tubuh 43,5 °C tidak lazim. Pastikan tidak salah ketik."),
        ({"saturasi": Decimal("89.9")}, "Saturasi oksigen 89,9% di bawah batas wajar (< 90%)."),
        # Tepi batas salah ketik dari prototipe (lib/vital-warnings.ts).
        ({"td_sistolik": 260}, "Tekanan darah sistolik 260 mmHg melewati batas wajar (≥ 180 mmHg)."),
        ({"td_sistolik": 261}, "Tekanan darah sistolik 261 mmHg tidak lazim. Pastikan tidak salah ketik."),
        ({"td_sistolik": 40, "td_diastolik": 20}, "Tekanan darah sistolik 40 mmHg di bawah batas wajar (< 90 mmHg)."),
        (
            {"td_sistolik": 39, "td_diastolik": 20},
            "Tekanan darah sistolik 39 mmHg tidak lazim. Pastikan tidak salah ketik.",
        ),
        ({"nadi": 250}, "Nadi 250 x/menit melewati batas wajar (≥ 130 x/menit)."),
        ({"nadi": 20}, "Nadi 20 x/menit di bawah batas wajar (< 50 x/menit)."),
        ({"nadi": 19}, "Nadi 19 x/menit tidak lazim. Pastikan tidak salah ketik."),
        ({"laju_napas": 5}, "Laju napas 5 x/menit di bawah batas wajar (< 10 x/menit)."),
        ({"laju_napas": 60}, "Laju napas 60 x/menit melewati batas wajar (≥ 30 x/menit)."),
        ({"laju_napas": 61}, "Laju napas 61 x/menit tidak lazim. Pastikan tidak salah ketik."),
        ({"suhu": Decimal("43.0")}, "Suhu tubuh 43 °C melewati batas wajar (≥ 39 °C)."),
        ({"suhu": Decimal("43.1")}, "Suhu tubuh 43,1 °C tidak lazim. Pastikan tidak salah ketik."),
        ({"suhu": Decimal("30.0")}, "Suhu tubuh 30 °C di bawah batas wajar (< 35 °C)."),
        ({"suhu": Decimal("29.9")}, "Suhu tubuh 29,9 °C tidak lazim. Pastikan tidak salah ketik."),
    ],
)
def test_batas_peringatan_per_tanda_vital(ubah, pesan):
    tv = TandaVital.model_validate({**TANDA_VITAL_NORMAL, **ubah})
    assert [p.pesan for p in PeringatanVital.periksa(tv)] == [pesan]


@pytest.mark.parametrize(
    ("diastolik", "pesan"),
    [
        (180, "Tekanan darah diastolik 180 mmHg melewati batas wajar (≥ 120 mmHg)."),
        (181, "Tekanan darah diastolik 181 mmHg tidak lazim. Pastikan tidak salah ketik."),
    ],
)
def test_tepi_salah_ketik_diastolik(diastolik, pesan):
    tv = TandaVital.model_validate({**TANDA_VITAL_NORMAL, "td_sistolik": 200, "td_diastolik": diastolik})
    pesan_diastolik = [p.pesan for p in PeringatanVital.periksa(tv) if p.field == "tanda_vital.td_diastolik"]
    assert pesan_diastolik == [pesan]


def test_nilai_tepat_di_bawah_ambang_atas_tidak_diberi_peringatan():
    tepi = {"td_sistolik": 179, "td_diastolik": 119, "nadi": 129, "laju_napas": 29, "suhu": 38.9, "saturasi": 100}
    assert PeringatanVital.periksa(TandaVital.model_validate(tepi)) == []


def test_nilai_normal_di_tepi_batas_tidak_diberi_peringatan():
    tepi = {"td_sistolik": 90, "td_diastolik": 60, "nadi": 50, "laju_napas": 10, "suhu": 35, "saturasi": 90}
    assert PeringatanVital.periksa(TandaVital.model_validate(tepi)) == []


def test_diastolik_tidak_lebih_rendah_dari_sistolik():
    tv = TandaVital.model_validate({**TANDA_VITAL_NORMAL, "td_sistolik": 100, "td_diastolik": 100})
    [peringatan] = PeringatanVital.periksa(tv)
    assert peringatan.field == "tanda_vital.td_diastolik"
    assert "tidak lebih rendah dari sistolik" in peringatan.pesan


def test_peringatan_untuk_pasien_anak(client, perawat, sesi_db):
    pengguna, header = perawat
    lahir = date(hari_ini().year - 16, 1, 1)
    pasien = Pasien(
        didaftarkan_oleh=pengguna.id_pengguna, nama="Anak", tanggal_lahir=lahir, jenis_kelamin=JenisKelamin.LAKI_LAKI
    )
    sesi_db.add(pasien)
    sesi_db.flush()
    kunjungan = Kunjungan(id_pasien=pasien.id_pasien)
    sesi_db.add(kunjungan)
    sesi_db.commit()

    isi = client.post(_url(kunjungan), json=_isian(), headers=header).get_json()
    [peringatan] = isi["peringatan"]
    assert peringatan["field"] is None
    assert "pasien ICU dewasa" in peringatan["pesan"]


# ---------------------------------------------------------------- aturan cadangan (TC-09)


def test_tanpa_model_penilaian_dari_news2(app_tanpa_model, buat_pengguna, kunjungan):
    klien = app_tanpa_model.test_client()
    header = header_masuk(klien, buat_pengguna(Peran.PERAWAT).email)
    isian = _isian(tanda_vital={"nadi": 125, "laju_napas": 30})  # napas 3 + nadi 2 = 5
    respons = klien.post(_url(kunjungan), json=isian, headers=header)

    assert respons.status_code == 201
    isi = respons.get_json()
    assert isi["sumber_rekomendasi"] == "aturan"
    assert isi["risk_level"] == "tinggi"
    assert isi["skor_news2"] == 5
    assert isi["peluang_perburukan"] is None
    penjelasan = isi["penjelasan_ai"]
    assert (penjelasan["versi_model"], penjelasan["peluang_perburukan"], penjelasan["level_model"]) == (
        None,
        None,
        None,
    )
    assert penjelasan["faktor"] == []
    assert [f["kontribusi"] for f in penjelasan["komponen_news2"]] == [3, 2]

    kesehatan = klien.get("/api/v1/health")
    assert kesehatan.status_code == 200
    assert kesehatan.get_json()["status"] == "degraded"
    assert kesehatan.get_json()["komponen"]["model_perburukan"] == "gagal"


def test_news2_memakai_ambang_dari_konfigurasi(app_tanpa_model, buat_pengguna, kunjungan, sesi_db):
    sesi_db.execute(update(Konfigurasi).values(ambang_kritis=12, ambang_tinggi=10, ambang_sedang=8))
    sesi_db.commit()
    klien = app_tanpa_model.test_client()
    header = header_masuk(klien, buat_pengguna(Peran.PERAWAT).email)
    # Skor 5 di bawah ambang sedang 8, tetapi laju napas bernilai 3 (red score) sehingga minimal sedang.
    isian = _isian(tanda_vital={"nadi": 125, "laju_napas": 30})
    assert klien.post(_url(kunjungan), json=isian, headers=header).get_json()["risk_level"] == "sedang"
    isian = _isian(tanda_vital={"nadi": 125})
    assert klien.post(_url(kunjungan), json=isian, headers=header).get_json()["risk_level"] == "rendah"


def test_model_error_saat_dipakai_beralih_ke_aturan(client, perawat, kunjungan, monkeypatch, caplog):
    def rusak(self, fitur):
        raise RuntimeError("SHAP gagal")

    monkeypatch.setattr(klasifikasi.RandomForestClassifier, "klasifikasi", rusak)
    _, header = perawat
    isi = client.post(_url(kunjungan), json=_isian(), headers=header).get_json()
    assert isi["sumber_rekomendasi"] == "aturan"
    assert isi["peluang_perburukan"] is None
    assert "memakai NEWS2 saja" in caplog.text


# ---------------------------------------------------------------- id_pemindaian (keputusan K17)


def _pemindaian(sesi_db, pemindai, nilai_terbaca, **kolom):
    pemindaian = PemindaianAlat(
        dipindai_oleh=pemindai.id_pengguna,
        jenis_alat=kolom.pop("jenis_alat", JenisAlat.TENSIMETER),
        nilai_terbaca=nilai_terbaca,
        keyakinan=Decimal("0.95"),
        **kolom,
    )
    sesi_db.add(pemindaian)
    sesi_db.commit()
    return pemindaian


def test_pemindaian_sebagian_membuat_sumber_campuran(client, perawat, kunjungan, sesi_db):
    pengguna, header = perawat
    tensi = _pemindaian(sesi_db, pengguna, {"td_sistolik": 121, "td_diastolik": 79, "nadi": 80})
    isi = client.post(_url(kunjungan), json=_isian(id_pemindaian=[str(tensi.id_pemindaian)]), headers=header).get_json()

    assert isi["sumber_tanda_vital"] == "campuran"
    sesi_db.refresh(tensi)
    assert str(tensi.id_triase) == isi["id_triase"]
    # Yang disimpan adalah nilai akhir yang dikirim perawat, sebagai bahan evaluasi akurasi pembaca layar.
    assert tensi.nilai_dikonfirmasi == {"nadi": 82, "td_diastolik": 80, "td_sistolik": 120}


def test_pemindaian_semua_kolom_membuat_sumber_pemindaian(client, perawat, kunjungan, sesi_db):
    pengguna, header = perawat
    monitor = _pemindaian(
        sesi_db,
        pengguna,
        {"td_sistolik": 120, "td_diastolik": 80, "nadi": 82, "laju_napas": 18, "saturasi": 98, "lain": 1},
        jenis_alat=JenisAlat.BEDSIDE_MONITOR,
    )
    termo = _pemindaian(sesi_db, pengguna, {"suhu": 36.8}, jenis_alat=JenisAlat.TERMOMETER)
    isian = _isian(id_pemindaian=[str(monitor.id_pemindaian), str(termo.id_pemindaian)])
    isi = client.post(_url(kunjungan), json=isian, headers=header).get_json()
    assert isi["sumber_tanda_vital"] == "pemindaian"
    sesi_db.refresh(termo)
    assert termo.nilai_dikonfirmasi == {"suhu": 36.8}


def test_pemindaian_yang_tidak_sah_ditolak(client, perawat, masuk, kunjungan, sesi_db):
    pengguna, header = perawat
    lain, _ = masuk(Peran.PERAWAT)
    milik_lain = _pemindaian(sesi_db, lain, {"saturasi": 98})
    triase_lama = Triase(
        id_kunjungan=kunjungan.id_kunjungan,
        jenis="awal",
        dibuat_oleh=pengguna.id_pengguna,
        tingkat_kesadaran="A",
        td_sistolik=120,
        td_diastolik=80,
        nadi=80,
        laju_napas=18,
        suhu=Decimal("36.5"),
        saturasi=Decimal("98"),
        sumber_tanda_vital="manual",
        skor_news2=0,
        risk_level=RiskLevel.RENDAH,
        sumber_rekomendasi="aturan",
        penjelasan_ai=PENJELASAN_KOSONG,
    )
    sesi_db.add(triase_lama)
    sesi_db.flush()
    terpakai = _pemindaian(sesi_db, pengguna, {"saturasi": 98}, id_triase=triase_lama.id_triase)

    isian = _isian(id_pemindaian=[str(uuid.uuid4()), str(milik_lain.id_pemindaian), str(terpakai.id_pemindaian)])
    respons = client.post(_url(kunjungan), json=isian, headers=header)
    assert respons.status_code == 422
    assert respons.get_json()["errors"] == [
        {"field": "id_pemindaian.0", "pesan": "Hasil pemindaian tidak ditemukan."},
        {"field": "id_pemindaian.1", "pesan": "Hasil pemindaian tidak ditemukan."},
        {"field": "id_pemindaian.2", "pesan": "Hasil pemindaian ini sudah dipakai triase lain."},
    ]


def test_id_pemindaian_ganda_ditolak(client, perawat, kunjungan):
    _, header = perawat
    sama = str(uuid.uuid4())
    respons = client.post(_url(kunjungan), json=_isian(id_pemindaian=[sama, sama]), headers=header)
    assert respons.get_json()["errors"] == [
        {"field": "id_pemindaian", "pesan": "ID pemindaian tidak boleh dikirim lebih dari sekali."}
    ]


# ---------------------------------------------------------------- GET /triase/{id}


@pytest.mark.parametrize("peran", [Peran.PERAWAT, Peran.DOKTER])
def test_detail_triase_untuk_perawat_dan_dokter(client, perawat, masuk, kunjungan, peran):
    _, header_perawat = perawat
    dibuat = client.post(_url(kunjungan), json=_isian(tanda_vital={"saturasi": 85}), headers=header_perawat).get_json()
    _, header = masuk(peran)
    respons = client.get(f"/api/v1/triase/{dibuat['id_triase']}", headers=header)
    assert respons.status_code == 200
    # Bentuknya sama dengan respons POST; peringatan dihitung ulang dari tanda vital tersimpan.
    assert respons.get_json() == dibuat


def test_detail_triase_memuat_alasan_validasi_terakhir(client, perawat, masuk, kunjungan, sesi_db):
    _, header = perawat
    dibuat = client.post(_url(kunjungan), json=_isian(), headers=header).get_json()
    dokter, header_dokter = masuk(Peran.DOKTER)
    id_triase = uuid.UUID(dibuat["id_triase"])
    waktu = sekarang()
    # Yang lebih baru disisipkan lebih dulu, supaya urutan sisip tidak menentukan hasil.
    for aksi, catatan, menit in ((AksiAudit.KOREKSI, "Sesak bertambah", 0), (AksiAudit.AJUKAN_REVIEW, "Ragu-ragu", 5)):
        log = LogAudit(id_aktor=dokter.id_pengguna, id_triase=id_triase, aksi=aksi, catatan=catatan)
        log.waktu = waktu - timedelta(minutes=menit)
        sesi_db.add(log)
    sesi_db.commit()
    isi = client.get(f"/api/v1/triase/{id_triase}", headers=header_dokter).get_json()
    assert isi["catatan_validasi_terakhir"] == "Sesak bertambah"


def test_detail_triase_tidak_ditemukan(client, perawat):
    _, header = perawat
    respons = client.get(f"/api/v1/triase/{uuid.uuid4()}", headers=header)
    assert respons.status_code == 404


def test_admin_tidak_membaca_detail_triase(client, masuk):
    _, header = masuk(Peran.ADMIN)
    assert client.get(f"/api/v1/triase/{uuid.uuid4()}", headers=header).status_code == 403


def test_usia_di_detail_dihitung_pada_tanggal_triase(client, perawat, sesi_db):
    """Observasi lama yang dibuka setelah ulang tahun pasien tetap memakai usia saat diobservasi (K15)."""
    pengguna, header = perawat
    lahir = date(hari_ini().year - 18, hari_ini().month, 1)
    pasien = Pasien(
        didaftarkan_oleh=pengguna.id_pengguna, nama="Remaja", tanggal_lahir=lahir, jenis_kelamin=JenisKelamin.PEREMPUAN
    )
    sesi_db.add(pasien)
    sesi_db.flush()
    kunjungan = Kunjungan(id_pasien=pasien.id_pasien)
    sesi_db.add(kunjungan)
    sesi_db.commit()
    isi = client.post(_url(kunjungan), json=_isian(), headers=header).get_json()
    assert isi["pasien"]["usia"] == 18
    assert isi["peringatan"] == []

    sesi_db.execute(
        update(Triase)
        .where(Triase.id_triase == uuid.UUID(isi["id_triase"]))
        .values(waktu_triase=sekarang() - timedelta(days=366))
    )
    sesi_db.commit()
    detail = client.get(f"/api/v1/triase/{isi['id_triase']}", headers=header).get_json()
    assert detail["pasien"]["usia"] == 17
    assert "Pasien berusia 17 tahun" in detail["peringatan"][0]["pesan"]


def test_karakter_kontrol_di_catatan_ditolak_tetapi_baris_baru_boleh(client, perawat, kunjungan):
    _, header = perawat
    respons = client.post(_url(kunjungan), json=_isian(catatan="Gelisah\x00 sejak pagi"), headers=header)
    assert respons.status_code == 422
    assert respons.get_json()["errors"] == [
        {"field": "catatan", "pesan": "Catatan berisi karakter yang tidak diizinkan."}
    ]
    respons = client.post(_url(kunjungan), json=_isian(catatan="Gelisah\nsejak pagi"), headers=header)
    assert respons.status_code == 201


def test_catatan_kosong_disimpan_sebagai_null(client, perawat, kunjungan):
    _, header = perawat
    assert client.post(_url(kunjungan), json=_isian(catatan="   "), headers=header).get_json()["catatan"] is None


def test_detail_memuat_nomor_bed(client, perawat, buat_kunjungan):
    _, header = perawat
    kunjungan = buat_kunjungan(nomor_bed="ICU-3")
    assert client.post(_url(kunjungan), json=_isian(), headers=header).get_json()["nomor_bed"] == "ICU-3"
