"""ModelRegistry, NEWS2, Random Forest peluang perburukan + SHAP, dan penyusun penjelasan (FR-05)."""

import logging
import math
from dataclasses import replace
from decimal import Decimal

import joblib
import numpy as np
import pytest

from app.ai import registry as modul_registry
from app.ai.klasifikasi import (
    KODE_JENIS_KELAMIN,
    DataObservasi,
    FallbackClassifier,
    HasilModel,
    HasilPenilaian,
    RandomForestClassifier,
    RuleBasedClassifier,
    buat_klasifikator,
    level_tertinggi,
)
from app.ai.news2 import (
    SKOR_MAKSIMUM,
    AmbangNews2,
    hitung_news2,
    level_news2,
    poin_kesadaran,
    poin_laju_napas,
    poin_nadi,
    poin_saturasi,
    poin_sistolik,
    poin_suhu,
)
from app.ai.penjelasan import Faktor, LabelFitur, PenyusunPenjelasan, format_angka
from app.ai.registry import (
    FITUR_MODEL,
    BundleTidakSesuaiError,
    ModelPerburukan,
    ModelRegistry,
    _periksa_bundle,
)
from app.config import Config
from app.models.enums import JenisKelamin, RiskLevel, SumberRekomendasi, TingkatKesadaran

AMBANG = AmbangNews2(kritis=7, tinggi=5, sedang=3)
NORMAL = DataObservasi(
    usia=45,
    jenis_kelamin=JenisKelamin.PEREMPUAN,
    tingkat_kesadaran=TingkatKesadaran.SADAR_PENUH,
    oksigen_tambahan=False,
    td_sistolik=120,
    td_diastolik=80,
    nadi=80,
    laju_napas=16,
    suhu=Decimal("36.8"),
    saturasi=Decimal("98.0"),
)
SYOK = replace(
    NORMAL,
    usia=70,
    jenis_kelamin=JenisKelamin.LAKI_LAKI,
    tingkat_kesadaran=TingkatKesadaran.RESPONS_SUARA,
    oksigen_tambahan=True,
    td_sistolik=84,
    td_diastolik=46,
    nadi=132,
    laju_napas=28,
    suhu=Decimal("39.2"),
    saturasi=Decimal("89.0"),
    laktat=Decimal("5.1"),
    kreatinin=Decimal("2.40"),
    trombosit=80,
    leukosit=Decimal("21.0"),
    bilirubin=Decimal("2.2"),
)


@pytest.fixture(scope="module")
def model() -> ModelPerburukan:
    registry = ModelRegistry()
    registry.muat(Config.MODEL_RF_PATH)
    assert registry.termuat
    return registry.model_perburukan


# ---------------------------------------------------------------- ModelRegistry


def test_registry_memuat_bundle_icu(model):
    assert model.versi == "rf-icu-physionet2019-v1"
    assert model.nama_fitur_transformasi == FITUR_MODEL
    assert model.ambang["sedang"] < model.ambang["tinggi"] < model.ambang["kritis"]
    # Satu thread per prediksi, supaya tidak berebut CPU dengan worker lain.
    assert model.rf.n_jobs == 1


@pytest.mark.parametrize(
    ("peluang", "level"),
    [(0.0, RiskLevel.RENDAH), (0.5, RiskLevel.SEDANG), (0.65, RiskLevel.TINGGI), (0.7, RiskLevel.KRITIS)],
)
def test_level_dari_peluang_mengikuti_ambang_bundle(peluang, level):
    model = ModelPerburukan(None, None, None, (), {"sedang": 0.5, "tinggi": 0.6, "kritis": 0.7}, "uji")
    assert model.level(peluang) == level


def test_registry_kosong_bila_path_tidak_diisi(caplog):
    registry = ModelRegistry()
    registry.muat(None)
    assert not registry.termuat
    assert registry.versi_model is None
    assert "MODEL_RF_PATH kosong" in caplog.text


def test_registry_kosong_bila_berkas_tidak_ada(tmp_path, caplog):
    registry = ModelRegistry()
    registry.muat(str(tmp_path / "tidak-ada.joblib"))
    assert not registry.termuat
    assert "tidak ditemukan" in caplog.text


def test_registry_kosong_bila_berkas_rusak(tmp_path, caplog):
    berkas = tmp_path / "rusak.joblib"
    berkas.write_bytes(b"bukan pickle")
    registry = ModelRegistry()
    with caplog.at_level(logging.ERROR):
        registry.muat(str(berkas))
    assert not registry.termuat
    assert "gagal dimuat" in caplog.text


def test_registry_menolak_bundle_igd_lama(tmp_path, caplog):
    berkas = tmp_path / "lama.joblib"
    joblib.dump({"model": None, "fitur": ["SBP"], "ambang": {}, "versi": "smarttriage-rf-v1.0.0"}, berkas)
    registry = ModelRegistry()
    registry.muat(str(berkas))
    assert not registry.termuat
    assert "Fitur bundle" in caplog.text


def test_registry_memakai_ulang_model_yang_sudah_dimuat(model):
    kedua = ModelRegistry()
    kedua.muat(Config.MODEL_RF_PATH)
    assert kedua.model_perburukan is model


class _RfTiruan:
    def __init__(self, kelas):
        self.classes_ = kelas


class _PipelineTiruan:
    def __init__(self, kelas):
        self.named_steps = {"model": _RfTiruan(kelas)}


def _bundle(**ubah):
    bundle = {
        "model": _PipelineTiruan([0, 1]),
        "fitur": list(modul_registry.FITUR_MODEL),
        "ambang": {"sedang": 0.4, "tinggi": 0.6, "kritis": 0.7},
        "versi": "uji",
    }
    bundle.update(ubah)
    return bundle


@pytest.mark.parametrize(
    ("bundle", "pesan"),
    [
        ([], "harus berupa dict"),
        ({"model": None}, "tidak punya kunci 'fitur'"),
        (_bundle(ambang={"sedang": 0.4}), "Ambang bundle harus berisi"),
        (_bundle(ambang=[0.4, 0.6, 0.7]), "Ambang bundle harus berisi"),
        (_bundle(ambang={"sedang": 0.7, "tinggi": 0.6, "kritis": 0.8}), "urut naik"),
        (_bundle(ambang={"sedang": 0.4, "tinggi": 0.6, "kritis": 1.2}), "urut naik"),
        (_bundle(model=_PipelineTiruan([0, 1, 2, 3])), "Kelas model"),
    ],
)
def test_pemeriksaan_isi_bundle(bundle, pesan):
    with pytest.raises(BundleTidakSesuaiError, match=pesan):
        _periksa_bundle(bundle)


def test_bundle_yang_sesuai_lolos_pemeriksaan():
    _periksa_bundle(_bundle())


# ---------------------------------------------------------------- NEWS2


@pytest.mark.parametrize(
    ("fungsi", "nilai_dan_poin"),
    [
        (poin_laju_napas, [(8, 3), (9, 1), (11, 1), (12, 0), (20, 0), (21, 2), (24, 2), (25, 3)]),
        (
            poin_saturasi,
            [(Decimal("91.9"), 3), (Decimal("92"), 2), (Decimal("93.9"), 2), (Decimal("94"), 1), (Decimal("96"), 0)],
        ),
        (poin_sistolik, [(90, 3), (91, 2), (100, 2), (101, 1), (110, 1), (111, 0), (219, 0), (220, 3)]),
        (poin_nadi, [(40, 3), (41, 1), (50, 1), (51, 0), (90, 0), (91, 1), (110, 1), (111, 2), (130, 2), (131, 3)]),
        (
            poin_suhu,
            [
                (Decimal("35.0"), 3),
                (Decimal("35.1"), 1),
                (Decimal("36.0"), 1),
                (Decimal("36.1"), 0),
                (Decimal("38.0"), 0),
                (Decimal("38.1"), 1),
                (Decimal("39.0"), 1),
                (Decimal("39.1"), 2),
            ],
        ),
    ],
)
def test_tabel_poin_news2(fungsi, nilai_dan_poin):
    assert [fungsi(nilai) for nilai, _ in nilai_dan_poin] == [poin for _, poin in nilai_dan_poin]


def test_poin_kesadaran():
    assert [poin_kesadaran(t) for t in TingkatKesadaran] == [0, 3, 3, 3]


def test_news2_normal_tanpa_komponen():
    hasil = RuleBasedClassifier(AMBANG).klasifikasi(NORMAL)
    assert (hasil.skor, hasil.level, hasil.komponen, hasil.ada_poin_merah) == (0, RiskLevel.RENDAH, [], False)


def test_news2_skor_maksimum_dan_urutan_komponen():
    hasil = hitung_news2(
        laju_napas=30,
        saturasi=Decimal("85"),
        oksigen_tambahan=True,
        td_sistolik=80,
        nadi=140,
        tingkat_kesadaran=TingkatKesadaran.TIDAK_RESPONS,
        suhu=Decimal("34.5"),
        ambang=AMBANG,
    )
    assert hasil.skor == SKOR_MAKSIMUM == 20
    assert hasil.level == RiskLevel.KRITIS
    assert [f.kontribusi for f in hasil.komponen] == [3, 3, 3, 3, 3, 3, 2]
    assert hasil.komponen[-1].label == "Mendapat oksigen tambahan"
    assert "Kesadaran U (tidak respons)" in [f.label for f in hasil.komponen]


@pytest.mark.parametrize(
    ("skor", "merah", "level"),
    [
        (0, False, RiskLevel.RENDAH),
        (2, False, RiskLevel.RENDAH),
        (3, False, RiskLevel.SEDANG),
        (3, True, RiskLevel.SEDANG),
        (4, True, RiskLevel.SEDANG),
        (5, False, RiskLevel.TINGGI),
        (6, True, RiskLevel.TINGGI),
        (7, False, RiskLevel.KRITIS),
    ],
)
def test_level_news2(skor, merah, level):
    assert level_news2(skor, merah, AMBANG) == level


def test_satu_parameter_merah_minimal_sedang():
    hasil = RuleBasedClassifier(AMBANG).klasifikasi(replace(NORMAL, laju_napas=8))
    assert (hasil.skor, hasil.ada_poin_merah, hasil.level) == (3, True, RiskLevel.SEDANG)
    ambang_tinggi = AmbangNews2(kritis=12, tinggi=10, sedang=8)
    assert RuleBasedClassifier(ambang_tinggi).klasifikasi(replace(NORMAL, laju_napas=8)).level == RiskLevel.SEDANG
    assert RuleBasedClassifier(ambang_tinggi).klasifikasi(replace(NORMAL, laju_napas=22)).level == RiskLevel.RENDAH


# ---------------------------------------------------------------- Random Forest + SHAP


def test_random_forest_mengembalikan_peluang_dan_tiga_faktor(model):
    hasil = RandomForestClassifier(model).klasifikasi(SYOK)
    assert 0 <= hasil.peluang <= 1
    assert hasil.level == model.level(hasil.peluang)
    assert hasil.versi == "rf-icu-physionet2019-v1"
    assert len(hasil.faktor) == 3
    assert all(f.fitur in FITUR_MODEL and f.arah in {"naik", "turun"} for f in hasil.faktor)
    assert [abs(f.kontribusi) for f in hasil.faktor] == sorted((abs(f.kontribusi) for f in hasil.faktor), reverse=True)


def test_pasien_syok_lebih_berisiko_dari_pasien_stabil(model):
    stabil = RandomForestClassifier(model).klasifikasi(NORMAL)
    syok = RandomForestClassifier(model).klasifikasi(SYOK)
    assert syok.peluang > stabil.peluang
    assert syok.level in {RiskLevel.TINGGI, RiskLevel.KRITIS}
    assert stabil.level in {RiskLevel.RENDAH, RiskLevel.SEDANG}


def test_hasil_sama_dengan_pipeline_pelatihan(model):
    """Baris yang disusun backend menghasilkan peluang yang sama dengan pipeline hasil ai_training."""
    import pandas as pd

    bundle = joblib.load(Config.MODEL_RF_PATH)
    baris = pd.DataFrame([SYOK.baris_model()], columns=bundle["fitur"])
    harapan = float(bundle["model"].predict_proba(baris)[0, 1])
    assert RandomForestClassifier(model).klasifikasi(SYOK).peluang == pytest.approx(harapan)


def test_nilai_shap_menjumlah_ke_peluang(model):
    import pandas as pd

    x = model.prep.transform(pd.DataFrame([SYOK.baris_model()], columns=list(FITUR_MODEL)))
    nilai = np.asarray(model.explainer.shap_values(x))[0, :, 1]
    dasar = np.asarray(model.explainer.expected_value)[1]
    assert dasar + nilai.sum() == pytest.approx(model.rf.predict_proba(x)[0, 1], abs=1e-6)


def test_lab_kosong_tidak_dijadikan_faktor(model):
    hasil = RandomForestClassifier(model).klasifikasi(NORMAL)
    assert {f.fitur for f in hasil.faktor}.isdisjoint({"laktat", "kreatinin", "trombosit", "leukosit", "bilirubin"})


def test_baris_model_memakai_kode_dan_rumus_pelatihan():
    baris = SYOK.baris_model()
    assert list(baris) == list(FITUR_MODEL)
    assert baris["map"] == (84 + 2 * 46) / 3
    assert baris["shock_index"] == 132 / 84
    assert baris["jenis_kelamin"] == KODE_JENIS_KELAMIN[JenisKelamin.LAKI_LAKI] == 1
    kosong = NORMAL.baris_model()
    assert math.isnan(kosong["laktat"])
    assert kosong["jenis_kelamin"] == 0


def test_nilai_model_untuk_label():
    nilai = SYOK.nilai_model()
    assert (nilai["map"], nilai["shock_index"], nilai["jenis_kelamin"]) == (58.7, 1.57, "laki_laki")
    assert nilai["laktat"] == 5.1
    tanpa_sistolik = replace(NORMAL, td_sistolik=0)
    assert tanpa_sistolik.nilai_model()["shock_index"] is None
    assert math.isnan(tanpa_sistolik.baris_model()["shock_index"])


# ---------------------------------------------------------------- penggabungan NEWS2 dan model


class _ClassifierRusak:
    def klasifikasi(self, data):
        raise RuntimeError("model rusak")


def test_fallback_memakai_news2_bila_model_error(caplog):
    hasil = FallbackClassifier(utama=_ClassifierRusak(), cadangan=RuleBasedClassifier(AMBANG)).klasifikasi(NORMAL)
    assert hasil.sumber == SumberRekomendasi.ATURAN
    assert hasil.model is None
    assert hasil.peluang is None
    assert "memakai NEWS2 saja" in caplog.text


def test_fallback_memakai_news2_bila_model_tidak_ada():
    hasil = buat_klasifikator(None, AMBANG).klasifikasi(SYOK)
    assert hasil.sumber == SumberRekomendasi.ATURAN
    assert hasil.risk_level == RiskLevel.KRITIS
    assert hasil.penjelasan_json()["faktor"] == []


def test_penilaian_memakai_model_bila_tersedia(model):
    hasil = buat_klasifikator(model, AMBANG).klasifikasi(NORMAL)
    assert hasil.sumber == SumberRekomendasi.MODEL
    assert hasil.peluang == Decimal(str(round(hasil.model.peluang, 4)))


@pytest.mark.parametrize(
    ("news2", "model", "akhir"),
    [
        (RiskLevel.KRITIS, RiskLevel.RENDAH, RiskLevel.KRITIS),
        (RiskLevel.RENDAH, RiskLevel.TINGGI, RiskLevel.TINGGI),
        (RiskLevel.SEDANG, RiskLevel.SEDANG, RiskLevel.SEDANG),
    ],
)
def test_level_akhir_adalah_yang_tertinggi(news2, model, akhir):
    hasil_news2 = RuleBasedClassifier(AMBANG).klasifikasi(NORMAL)
    hasil = HasilPenilaian(
        news2=replace(hasil_news2, level=news2), model=HasilModel(peluang=0.5, level=model, faktor=[], versi="uji")
    )
    assert hasil.risk_level == akhir
    assert level_tertinggi(news2, model) == akhir


def test_penjelasan_json(model):
    isi = buat_klasifikator(model, AMBANG).klasifikasi(SYOK).penjelasan_json()
    assert set(isi) == {
        "versi_model",
        "skor_news2",
        "level_news2",
        "komponen_news2",
        "peluang_perburukan",
        "level_model",
        "faktor",
    }
    assert isi["level_news2"] == "kritis"
    assert isi["komponen_news2"][0] == {
        "fitur": "laju_napas",
        "label": "Laju napas 28 x/menit",
        "nilai": 28,
        "kontribusi": 3,
        "arah": "naik",
    }
    assert len(isi["faktor"]) == 3


# ---------------------------------------------------------------- label dan format


@pytest.mark.parametrize(
    ("nama", "nilai", "label"),
    [
        ("saturasi", 88.0, "Saturasi oksigen 88%"),
        ("suhu", 37.5, "Suhu tubuh 37,5 °C"),
        ("td_sistolik", 168, "Tekanan darah sistolik 168 mmHg"),
        ("td_diastolik", 102, "Tekanan darah diastolik 102 mmHg"),
        ("nadi", 118, "Nadi 118 x/menit"),
        ("laju_napas", 28, "Laju napas 28 x/menit"),
        ("usia", 45, "Usia 45 tahun"),
        ("jenis_kelamin", "laki_laki", "Jenis kelamin laki-laki"),
        ("map", 124.33, "Tekanan arteri rata-rata 124,3 mmHg"),
        ("laktat", 4.2, "Laktat 4,2 mmol/L"),
        ("kreatinin", 1.25, "Kreatinin 1,25 mg/dL"),
        ("trombosit", 95, "Trombosit 95 ribu/µL"),
        ("leukosit", 18.4, "Leukosit 18,4 ribu/µL"),
        ("bilirubin", 2.0, "Bilirubin total 2 mg/dL"),
        ("shock_index", 0.7, "Shock index 0,7"),
        ("shock_index", 1.25, "Shock index 1,25"),
    ],
)
def test_label_fitur(nama, nilai, label):
    assert LabelFitur.label(nama, nilai) == label


@pytest.mark.parametrize(
    ("nilai", "desimal", "teks"),
    [(98.0, 1, "98"), (37.5, 1, "37,5"), (Decimal("36.0"), 1, "36"), (0.704, 2, "0,7"), (124.666, 1, "124,7")],
)
def test_format_angka(nilai, desimal, teks):
    assert format_angka(nilai, desimal) == teks


def test_dari_shap_membuang_nilai_kosong_walau_kontribusinya_terbesar():
    nama = ("num__laktat", "nadi", "laju_napas", "suhu", "saturasi")
    nilai = {"laktat": None, "nadi": 80, "laju_napas": 16, "suhu": 36.8, "saturasi": 98.0}
    faktor = PenyusunPenjelasan.dari_shap([0.9, 0.2, -0.3, 0.1, 0.05], nama, nilai)
    assert [f.fitur for f in faktor] == ["laju_napas", "nadi", "suhu"]
    assert [f.arah for f in faktor] == ["turun", "naik", "naik"]


def test_faktor_ke_json():
    assert Faktor("nadi", "Nadi 80 x/menit", 80, 0.1, "naik").ke_json() == {
        "fitur": "nadi",
        "label": "Nadi 80 x/menit",
        "nilai": 80,
        "kontribusi": 0.1,
        "arah": "naik",
    }
