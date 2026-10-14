"""POST /kunjungan/{id}/triase dan GET /triase/{id} (FR-03, FR-05, SKPL TC-05 sampai TC-09)."""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from bantuan import header_masuk
from sqlalchemy import update

from app.ai import klasifikasi
from app.models import Konfigurasi, Kunjungan, LogAudit, Pasien, PemindaianAlat, Triase
from app.models.enums import (
    AksiAudit,
    JenisAlat,
    JenisKelamin,
    Peran,
    RiskLevel,
    StatusKunjungan,
)
from app.services.triase_service import PeringatanVital
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
    "keluhan_utama": "Pusing berputar",
    "gejala": "Pusing berputar sejak pagi, tidak muntah, masih bisa berjalan",
    "kategori_keluhan": "Pusing",
    "skala_nyeri": 3,
    "tingkat_kesadaran": "A",
    "tanda_vital": TANDA_VITAL_NORMAL,
}


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
    assert isi["peringatan"] == []
    assert isi["catatan_validasi_terakhir"] is None

    penjelasan = isi["penjelasan_ai"]
    assert penjelasan["versi_model"] == "smarttriage-rf-v1.0.0"
    assert len(penjelasan["faktor"]) == 3
    assert set(penjelasan["probabilitas"]) == {"rendah", "sedang", "tinggi", "kritis"}

    triase = sesi_db.get(Triase, uuid.UUID(isi["id_triase"]))
    assert triase.penjelasan_ai == penjelasan
    assert triase.kategori_keluhan.value == "Pusing"
    # Membuat triase tidak menulis log audit; yang diaudit adalah validasinya (Desain Gambar 2.9).
    assert sesi_db.query(LogAudit).count() == 0


def test_triase_kedua_dicatat_sebagai_triase_ulang(client, perawat, kunjungan):
    _, header = perawat
    assert client.post(_url(kunjungan), json=_isian(), headers=header).get_json()["jenis"] == "awal"
    assert client.post(_url(kunjungan), json=_isian(), headers=header).get_json()["jenis"] == "ulang"


def test_pasien_gawat_mendapat_level_tinggi(client, perawat, kunjungan):
    _, header = perawat
    isian = _isian(
        kategori_keluhan="Sesak napas atau batuk",
        tingkat_kesadaran="P",
        tanda_vital={"td_sistolik": 85, "td_diastolik": 50, "nadi": 135, "laju_napas": 32, "saturasi": 84},
    )
    isi = client.post(_url(kunjungan), json=isian, headers=header).get_json()
    assert isi["risk_level"] in {"tinggi", "kritis"}


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
        ({"skala_nyeri": 11}, [{"field": "skala_nyeri", "pesan": "Skala nyeri maksimal 10."}]),
        ({"skala_nyeri": None}, [{"field": "skala_nyeri", "pesan": "Skala nyeri harus berupa bilangan bulat."}]),
        ({"gejala": "pusing"}, [{"field": "gejala", "pesan": "Gejala minimal 10 karakter."}]),
        ({"keluhan_utama": "   "}, [{"field": "keluhan_utama", "pesan": "Keluhan utama wajib diisi."}]),
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


@pytest.mark.parametrize("field", ["kategori_keluhan", "skala_nyeri", "tingkat_kesadaran", "tanda_vital"])
def test_isian_wajib(client, perawat, kunjungan, field):
    _, header = perawat
    isian = _isian()
    del isian[field]
    respons = client.post(_url(kunjungan), json=isian, headers=header)
    assert respons.status_code == 422
    assert respons.get_json()["errors"][0]["field"] == field
    assert respons.get_json()["errors"][0]["pesan"].endswith("wajib diisi.")


def test_kategori_keluhan_harus_salah_satu_dari_18_kategori(client, perawat, kunjungan):
    _, header = perawat
    respons = client.post(_url(kunjungan), json=_isian(kategori_keluhan="Batuk"), headers=header)
    [galat] = respons.get_json()["errors"]
    assert galat["field"] == "kategori_keluhan"
    assert "'Nyeri dada'" in galat["pesan"]


def test_kunjungan_tidak_ditemukan(client, perawat):
    _, header = perawat
    respons = client.post(f"/api/v1/kunjungan/{uuid.uuid4()}/triase", json=_isian(), headers=header)
    assert respons.status_code == 404
    assert respons.get_json()["type"] == Tipe.TIDAK_DITEMUKAN


def test_id_kunjungan_bukan_uuid_dibalas_404(client, perawat):
    _, header = perawat
    assert client.post("/api/v1/kunjungan/123/triase", json=_isian(), headers=header).status_code == 404


@pytest.mark.parametrize("status", [StatusKunjungan.DITANGANI, StatusKunjungan.SELESAI])
def test_kunjungan_yang_sudah_ditangani_tidak_bisa_ditriase(client, perawat, kunjungan, sesi_db, status):
    _, header = perawat
    sesi_db.execute(update(Kunjungan).where(Kunjungan.id_kunjungan == kunjungan.id_kunjungan).values(status=status))
    sesi_db.commit()
    respons = client.post(_url(kunjungan), json=_isian(), headers=header)
    assert respons.status_code == 409
    assert respons.get_json()["type"] == Tipe.KONFLIK


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
    lahir = date(hari_ini().year - 8, 1, 1)
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
    assert "remaja dan dewasa" in peringatan["pesan"]


# ---------------------------------------------------------------- aturan cadangan (TC-09)


def test_tanpa_model_rekomendasi_dari_aturan_cadangan(app_tanpa_model, buat_pengguna, kunjungan):
    klien = app_tanpa_model.test_client()
    header = header_masuk(klien, buat_pengguna(Peran.PERAWAT).email)
    isian = _isian(tanda_vital={"nadi": 125, "laju_napas": 30})  # 4 poin
    respons = klien.post(_url(kunjungan), json=isian, headers=header)

    assert respons.status_code == 201
    isi = respons.get_json()
    assert isi["sumber_rekomendasi"] == "aturan"
    assert isi["risk_level"] == "tinggi"
    assert isi["penjelasan_ai"]["versi_model"] is None
    assert isi["penjelasan_ai"]["probabilitas"] is None
    assert [f["kontribusi"] for f in isi["penjelasan_ai"]["faktor"]] == [2, 2]

    kesehatan = klien.get("/api/v1/health")
    assert kesehatan.status_code == 200
    assert kesehatan.get_json()["status"] == "degraded"
    assert kesehatan.get_json()["komponen"]["model_triase"] == "gagal"


def test_aturan_cadangan_memakai_ambang_dari_konfigurasi(app_tanpa_model, buat_pengguna, kunjungan, sesi_db):
    sesi_db.execute(update(Konfigurasi).values(ambang_kritis=12, ambang_tinggi=10, ambang_sedang=8))
    sesi_db.commit()
    klien = app_tanpa_model.test_client()
    header = header_masuk(klien, buat_pengguna(Peran.PERAWAT).email)
    isian = _isian(tanda_vital={"nadi": 125, "laju_napas": 30})
    assert klien.post(_url(kunjungan), json=isian, headers=header).get_json()["risk_level"] == "rendah"


def test_model_error_saat_dipakai_beralih_ke_aturan(client, perawat, kunjungan, monkeypatch, caplog):
    def rusak(self, fitur):
        raise RuntimeError("SHAP gagal")

    monkeypatch.setattr(klasifikasi.RandomForestClassifier, "klasifikasi", rusak)
    _, header = perawat
    isi = client.post(_url(kunjungan), json=_isian(), headers=header).get_json()
    assert isi["sumber_rekomendasi"] == "aturan"
    assert "memakai aturan cadangan" in caplog.text


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
        keluhan_utama="x",
        gejala="gejala lama pasien",
        tingkat_kesadaran="A",
        td_sistolik=120,
        td_diastolik=80,
        nadi=80,
        laju_napas=18,
        suhu=Decimal("36.5"),
        saturasi=Decimal("98"),
        sumber_tanda_vital="manual",
        risk_level=RiskLevel.RENDAH,
        sumber_rekomendasi="aturan",
        penjelasan_ai={"versi_model": None, "faktor": [], "probabilitas": None},
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
    """Triase lama yang dibuka setelah ulang tahun pasien tetap memakai usia saat ditriase (K15)."""
    pengguna, header = perawat
    lahir = date(hari_ini().year - 15, hari_ini().month, 1)
    pasien = Pasien(
        didaftarkan_oleh=pengguna.id_pengguna, nama="Remaja", tanggal_lahir=lahir, jenis_kelamin=JenisKelamin.PEREMPUAN
    )
    sesi_db.add(pasien)
    sesi_db.flush()
    kunjungan = Kunjungan(id_pasien=pasien.id_pasien)
    sesi_db.add(kunjungan)
    sesi_db.commit()
    isi = client.post(_url(kunjungan), json=_isian(), headers=header).get_json()
    assert isi["pasien"]["usia"] == 15
    assert isi["peringatan"] == []

    sesi_db.execute(
        update(Triase)
        .where(Triase.id_triase == uuid.UUID(isi["id_triase"]))
        .values(waktu_triase=sekarang() - timedelta(days=366))
    )
    sesi_db.commit()
    detail = client.get(f"/api/v1/triase/{isi['id_triase']}", headers=header).get_json()
    assert detail["pasien"]["usia"] == 14
    assert "Pasien berusia 14 tahun" in detail["peringatan"][0]["pesan"]


def test_karakter_kontrol_di_gejala_ditolak_tetapi_baris_baru_boleh(client, perawat, kunjungan):
    _, header = perawat
    respons = client.post(_url(kunjungan), json=_isian(gejala="Pusing berputar\x00 sejak pagi"), headers=header)
    assert respons.status_code == 422
    assert respons.get_json()["errors"] == [
        {"field": "gejala", "pesan": "Gejala berisi karakter yang tidak diizinkan."}
    ]
    respons = client.post(_url(kunjungan), json=_isian(gejala="Pusing berputar\nsejak pagi, mual"), headers=header)
    assert respons.status_code == 201
