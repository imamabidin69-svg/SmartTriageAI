"""ModelRegistry, klasifikator Random Forest + SHAP, aturan cadangan, dan penyusun penjelasan (FR-05)."""

import logging
import math
from dataclasses import replace
from decimal import Decimal

import joblib
import pytest

from app.ai import registry as modul_registry
from app.ai.klasifikasi import (
    SKOR_MAKSIMUM_ATURAN,
    AmbangAturan,
    FallbackClassifier,
    FiturTriase,
    RandomForestClassifier,
    RuleBasedClassifier,
    buat_klasifikator,
)
from app.ai.penjelasan import Faktor, LabelFitur, PenyusunPenjelasan, format_angka
from app.ai.registry import BundleTidakSesuaiError, ModelRegistry, ModelTriase, _periksa_bundle
from app.config import Config
from app.models.enums import JenisKelamin, KategoriKeluhan, RiskLevel, SumberRekomendasi, TingkatKesadaran

AMBANG = AmbangAturan(kritis=6, tinggi=4, sedang=2)
NORMAL = FiturTriase(
    usia=30,
    jenis_kelamin=JenisKelamin.PEREMPUAN,
    kategori_keluhan=KategoriKeluhan.PUSING,
    tingkat_kesadaran=TingkatKesadaran.SADAR_PENUH,
    skala_nyeri=2,
    td_sistolik=120,
    td_diastolik=80,
    nadi=80,
    laju_napas=16,
    suhu=Decimal("36.8"),
    saturasi=Decimal("99.0"),
    gejala="pusing berputar sejak pagi tanpa muntah",
)


@pytest.fixture(scope="module")
def model() -> ModelTriase:
    registry = ModelRegistry()
    registry.muat(Config.MODEL_RF_PATH)
    assert registry.termuat
    return registry.model_triase


# ---------------------------------------------------------------- ModelRegistry


def test_registry_memuat_bundle_prototipe(model):
    assert model.versi == "smarttriage-rf-v1.0.0"
    assert len(model.nama_fitur_transformasi) == 30
    # Satu thread per prediksi, supaya tidak berebut CPU dengan worker lain.
    assert model.rf.n_jobs == 1


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


def test_registry_menolak_bundle_yang_fiturnya_berbeda(tmp_path, caplog):
    berkas = tmp_path / "lain.joblib"
    joblib.dump(
        {"model": None, "fitur": ["SBP"], "urutan_level": [], "kategori_keluhan_dikenal": [], "versi": "x"}, berkas
    )
    registry = ModelRegistry()
    registry.muat(str(berkas))
    assert not registry.termuat
    assert "Fitur bundle" in caplog.text


def test_registry_memakai_ulang_model_yang_sudah_dimuat(model):
    kedua = ModelRegistry()
    kedua.muat(Config.MODEL_RF_PATH)
    assert kedua.model_triase is model


class _RfTiruan:
    def __init__(self, kelas):
        self.classes_ = kelas


class _PipelineTiruan:
    def __init__(self, kelas):
        self.named_steps = {"model": _RfTiruan(kelas)}


def _bundle(**ubah):
    bundle = {
        "model": _PipelineTiruan([0, 1, 2, 3]),
        "fitur": list(modul_registry.FITUR_MODEL),
        "urutan_level": ["rendah", "sedang", "tinggi", "kritis"],
        "kategori_keluhan_dikenal": [k.value for k in KategoriKeluhan],
        "versi": "uji",
    }
    bundle.update(ubah)
    return bundle


@pytest.mark.parametrize(
    ("bundle", "pesan"),
    [
        ([], "harus berupa dict"),
        ({"model": None}, "tidak punya kunci 'fitur'"),
        (_bundle(urutan_level=["kritis", "tinggi", "sedang", "rendah"]), "Urutan level"),
        (_bundle(kategori_keluhan_dikenal=["Lainnya"]), "Kategori keluhan"),
        (_bundle(model=_PipelineTiruan([1, 2, 3, 4])), "Kelas model"),
    ],
)
def test_pemeriksaan_isi_bundle(bundle, pesan):
    with pytest.raises(BundleTidakSesuaiError, match=pesan):
        _periksa_bundle(bundle)


def test_bundle_yang_sesuai_lolos_pemeriksaan():
    _periksa_bundle(_bundle())


# ---------------------------------------------------------------- Random Forest + SHAP


def test_random_forest_mengembalikan_tiga_faktor_berlabel(model):
    fitur = replace(
        NORMAL,
        usia=58,
        jenis_kelamin=JenisKelamin.LAKI_LAKI,
        kategori_keluhan=KategoriKeluhan.NYERI_DADA,
        skala_nyeri=7,
        td_sistolik=168,
        td_diastolik=102,
        nadi=118,
        laju_napas=28,
        suhu=Decimal("37.1"),
        saturasi=Decimal("91.0"),
    )
    hasil = RandomForestClassifier(model).klasifikasi(fitur)

    assert hasil.sumber == SumberRekomendasi.MODEL
    assert hasil.versi_model == "smarttriage-rf-v1.0.0"
    assert set(hasil.probabilitas) == {"rendah", "sedang", "tinggi", "kritis"}
    assert sum(hasil.probabilitas.values()) == pytest.approx(1, abs=1e-3)
    # Level yang dipilih adalah level dengan probabilitas tertinggi.
    assert hasil.risk_level == max(hasil.probabilitas, key=hasil.probabilitas.get)
    assert len(hasil.penjelasan) == 3
    kontribusi = [abs(f.kontribusi) for f in hasil.penjelasan]
    assert kontribusi == sorted(kontribusi, reverse=True)
    for faktor in hasil.penjelasan:
        assert faktor.arah in ("naik", "turun")
        assert faktor.label
    # Penjelasan tersimpan sebagai JSON biasa (tanpa tipe numpy atau Decimal).
    json_penjelasan = hasil.penjelasan_json()
    assert all(type(f["kontribusi"]) is float for f in json_penjelasan["faktor"])
    assert json_penjelasan["versi_model"] == "smarttriage-rf-v1.0.0"


def test_random_forest_menandai_pasien_tidak_respons(model):
    fitur = replace(NORMAL, tingkat_kesadaran=TingkatKesadaran.TIDAK_RESPONS, td_sistolik=80, td_diastolik=50)
    hasil = RandomForestClassifier(model).klasifikasi(fitur)
    assert hasil.risk_level in (RiskLevel.TINGGI, RiskLevel.KRITIS)


def test_fitur_yang_diimputasi_tidak_dijadikan_faktor(model):
    # Usia kosong diisi median oleh pipeline, dan shock index kosong bila sistolik 0.
    fitur = replace(NORMAL, usia=None, td_sistolik=0)
    hasil = RandomForestClassifier(model).klasifikasi(fitur)
    nama_faktor = {f.fitur for f in hasil.penjelasan}
    assert "Age" not in nama_faktor
    assert "shock_index" not in nama_faktor


def _prediksi_cara_prototipe(model, fitur):
    """Meniru ml-service/app.py: kode Sex dan Mental yang sama, fitur turunan tanpa pembulatan."""
    import pandas as pd

    baris = {
        "Sex": 1 if fitur.jenis_kelamin == JenisKelamin.PEREMPUAN else 2,
        "Age": fitur.usia,
        "kategori_keluhan": fitur.kategori_keluhan.value,
        "Mental": "AVPU".index(fitur.tingkat_kesadaran.value) + 1,
        "NRS_pain": fitur.skala_nyeri,
        "SBP": fitur.td_sistolik,
        "DBP": fitur.td_diastolik,
        "HR": fitur.nadi,
        "RR": fitur.laju_napas,
        "BT": float(fitur.suhu),
        "Saturation": float(fitur.saturasi),
    }
    baris["map"] = (baris["SBP"] + 2 * baris["DBP"]) / 3
    baris["shock_index"] = (baris["HR"] / baris["SBP"]) if baris["SBP"] else None
    x = model.prep.transform(pd.DataFrame([baris])[list(modul_registry.FITUR_MODEL)])
    return model.rf.predict_proba(x.toarray() if hasattr(x, "toarray") else x)[0]


def test_hasil_sama_dengan_cara_prototipe(model):
    """Input model harus sama persis dengan saat pelatihan, termasuk map dan shock index tanpa pembulatan."""
    import random

    acak = random.Random(42)  # noqa: S311 (data uji yang bisa diulang, bukan kriptografi)
    kasus = [
        # Kasus yang berbeda level bila fitur turunan dibulatkan dua desimal.
        replace(
            NORMAL,
            usia=25,
            jenis_kelamin=JenisKelamin.LAKI_LAKI,
            kategori_keluhan=KategoriKeluhan.LAINNYA,
            skala_nyeri=1,
            td_sistolik=154,
            td_diastolik=40,
            nadi=101,
            laju_napas=11,
            suhu=Decimal("39.5"),
            saturasi=Decimal("92"),
        )
    ]
    for _ in range(150):
        kasus.append(
            replace(
                NORMAL,
                usia=acak.randint(15, 95),
                jenis_kelamin=acak.choice(list(JenisKelamin)),
                kategori_keluhan=acak.choice(list(KategoriKeluhan)),
                tingkat_kesadaran=acak.choice(list(TingkatKesadaran)),
                skala_nyeri=acak.randint(0, 10),
                td_sistolik=acak.randint(70, 220),
                td_diastolik=acak.randint(40, 130),
                nadi=acak.randint(40, 160),
                laju_napas=acak.randint(8, 40),
                suhu=Decimal(acak.randint(350, 410)) / 10,
                saturasi=Decimal(acak.randint(80, 100)),
            )
        )
    for fitur in kasus:
        hasil = RandomForestClassifier(model).klasifikasi(fitur)
        proba = _prediksi_cara_prototipe(model, fitur)
        assert [hasil.probabilitas[level.value] for level in modul_registry.URUTAN_LEVEL] == pytest.approx(
            [round(float(p), 4) for p in proba], abs=1e-9
        )
        assert hasil.risk_level == modul_registry.URUTAN_LEVEL[int(proba.argmax())]


def test_faktor_shap_diambil_dari_kelas_yang_diprediksi(model):
    import numpy as np
    import pandas as pd

    fitur = replace(NORMAL, kategori_keluhan=KategoriKeluhan.NYERI_DADA, td_sistolik=168, nadi=118, laju_napas=28)
    hasil = RandomForestClassifier(model).klasifikasi(fitur)
    indeks = modul_registry.URUTAN_LEVEL.index(hasil.risk_level)

    x = model.prep.transform(pd.DataFrame([fitur.baris_model()], columns=list(modul_registry.FITUR_MODEL)))
    x = x.toarray() if hasattr(x, "toarray") else x
    shap_kelas = np.asarray(model.explainer.shap_values(x))[0, :, indeks]
    # Aditivitas SHAP: nilai dasar ditambah seluruh kontribusi sama dengan probabilitas level yang dipilih.
    dasar = np.asarray(model.explainer.expected_value)[indeks]
    assert dasar + shap_kelas.sum() == pytest.approx(hasil.probabilitas[hasil.risk_level.value], abs=1e-3)
    harapan = PenyusunPenjelasan.dari_shap(shap_kelas, model.nama_fitur_transformasi, x[0], fitur.nilai_model())
    assert hasil.penjelasan == harapan


def test_baris_model_tidak_membulatkan_fitur_turunan():
    fitur = replace(NORMAL, td_sistolik=154, td_diastolik=40, nadi=101)
    assert fitur.baris_model()["shock_index"] == 101 / 154
    assert fitur.baris_model()["map"] == (154 + 80) / 3
    assert fitur.nilai_model()["shock_index"] == 0.66
    baris = replace(NORMAL, td_sistolik=0, usia=None).baris_model()
    assert math.isnan(baris["shock_index"])
    assert math.isnan(baris["Age"])
    assert (baris["Sex"], baris["Mental"]) == (1, 1)


def test_dari_shap_membuang_nilai_kosong_walau_kontribusinya_terbesar():
    nama = ("angka__shock_index", "angka__Age", "angka__HR")
    faktor = PenyusunPenjelasan.dari_shap(
        [0.9, -0.8, 0.1], nama, [0.6, 57, 80], {"shock_index": None, "Age": None, "HR": 80}
    )
    assert [f.fitur for f in faktor] == ["HR"]


def test_nilai_model_menghitung_fitur_turunan():
    nilai = replace(NORMAL, td_sistolik=120, td_diastolik=90, nadi=96).nilai_model()
    assert nilai["map"] == 100
    assert nilai["shock_index"] == 0.8
    assert nilai["Sex"] == "perempuan"
    assert nilai["Mental"] == "A"
    assert replace(NORMAL, td_sistolik=0).nilai_model()["shock_index"] is None


# ---------------------------------------------------------------- aturan cadangan


def _aturan(**ubah):
    return RuleBasedClassifier(AMBANG).klasifikasi(replace(NORMAL, **ubah))


def test_aturan_tanpa_pemicu_memberi_satu_faktor_netral():
    hasil = _aturan()
    assert hasil.risk_level == RiskLevel.RENDAH
    assert hasil.sumber == SumberRekomendasi.ATURAN
    assert hasil.versi_model is None
    assert hasil.probabilitas is None
    assert [f.arah for f in hasil.penjelasan] == ["netral"]
    # Tidak mengklaim tanda vital normal, karena aturan tidak memeriksa misalnya suhu rendah.
    assert [f.label for f in hasil.penjelasan] == ["Tidak ada aturan risiko cadangan yang terpicu"]
    assert hasil.penjelasan_json()["faktor"][0]["kontribusi"] == 0


@pytest.mark.parametrize(
    ("ubah", "poin", "label"),
    [
        ({"saturasi": Decimal("91.9")}, 3, "Saturasi oksigen rendah (91,9%)"),
        ({"saturasi": Decimal("92.0")}, 1, "Saturasi oksigen agak rendah (92%)"),
        ({"saturasi": Decimal("95.0")}, 0, None),
        ({"td_sistolik": 180}, 3, "Tekanan darah sistolik ekstrem (180 mmHg)"),
        ({"td_sistolik": 89}, 3, "Tekanan darah sistolik ekstrem (89 mmHg)"),
        ({"td_sistolik": 150}, 1, "Tekanan darah sistolik tinggi (150 mmHg)"),
        ({"td_sistolik": 90}, 0, None),
        ({"nadi": 120}, 2, "Nadi tidak normal (120 x/menit)"),
        ({"nadi": 49}, 2, "Nadi tidak normal (49 x/menit)"),
        ({"suhu": Decimal("39.0")}, 2, "Demam tinggi (39 °C)"),
        ({"suhu": Decimal("37.8")}, 1, "Demam ringan (37,8 °C)"),
        ({"laju_napas": 28}, 2, "Laju napas tidak normal (28 x/menit)"),
        ({"laju_napas": 9}, 2, "Laju napas tidak normal (9 x/menit)"),
        ({"gejala": "Pasien mengeluh SESAK sejak tadi"}, 3, "Kata kunci gejala berisiko tinggi pada uraian keluhan"),
        ({"tingkat_kesadaran": TingkatKesadaran.RESPONS_SUARA}, 1, "Tingkat kesadaran V (respons terhadap suara)"),
        ({"tingkat_kesadaran": TingkatKesadaran.RESPONS_NYERI}, 3, "Tingkat kesadaran P (respons terhadap nyeri)"),
        ({"tingkat_kesadaran": TingkatKesadaran.TIDAK_RESPONS}, 3, "Tingkat kesadaran U (tidak respons)"),
        # Nilai tepi di sisi lain setiap batas, supaya < dan <= tidak tertukar (port persis lib/classify.ts).
        ({"saturasi": Decimal("94.9")}, 1, "Saturasi oksigen agak rendah (94,9%)"),
        ({"td_sistolik": 179}, 1, "Tekanan darah sistolik tinggi (179 mmHg)"),
        ({"td_sistolik": 149}, 0, None),
        ({"nadi": 119}, 0, None),
        ({"nadi": 50}, 0, None),
        ({"suhu": Decimal("38.9")}, 1, "Demam ringan (38,9 °C)"),
        ({"suhu": Decimal("37.7")}, 0, None),
        ({"laju_napas": 27}, 0, None),
        ({"laju_napas": 10}, 0, None),
        ({"gejala": "pendarahan hebat dari hidung"}, 3, "Kata kunci gejala berisiko tinggi pada uraian keluhan"),
        ({"gejala": "pasien mengeluh nyeri pada dada kanan"}, 0, None),
    ],
)
def test_poin_setiap_aturan(ubah, poin, label):
    terpicu = RuleBasedClassifier.aturan_terpicu(replace(NORMAL, **ubah))
    assert sum(f.kontribusi for f in terpicu) == poin
    if label:
        assert [f.label for f in terpicu] == [label]


def test_kata_kunci_gejala_dicatat_sebagai_nilai():
    terpicu = RuleBasedClassifier.aturan_terpicu(replace(NORMAL, gejala="kejang dua kali di rumah"))
    assert terpicu[0].fitur == "gejala"
    assert terpicu[0].nilai == "kejang"


@pytest.mark.parametrize(
    ("ubah", "level"),
    [
        ({"saturasi": Decimal("94")}, RiskLevel.RENDAH),  # 1 poin
        ({"nadi": 125}, RiskLevel.SEDANG),  # 2 poin
        ({"nadi": 125, "saturasi": Decimal("94")}, RiskLevel.SEDANG),  # 3 poin
        ({"nadi": 125, "laju_napas": 30}, RiskLevel.TINGGI),  # 4 poin
        ({"td_sistolik": 185, "saturasi": Decimal("90")}, RiskLevel.KRITIS),  # 6 poin
        # Pasien tidak respons dengan tanda vital normal tidak lagi dinilai rendah (keputusan K5).
        ({"tingkat_kesadaran": TingkatKesadaran.TIDAK_RESPONS}, RiskLevel.SEDANG),
    ],
)
def test_level_aturan_mengikuti_ambang(ubah, level):
    assert _aturan(**ubah).risk_level == level


def test_ambang_aturan_diambil_dari_konfigurasi():
    fitur = replace(NORMAL, nadi=125, laju_napas=30)  # 4 poin
    assert RuleBasedClassifier(AmbangAturan(6, 4, 2)).klasifikasi(fitur).risk_level == RiskLevel.TINGGI
    assert RuleBasedClassifier(AmbangAturan(10, 8, 5)).klasifikasi(fitur).risk_level == RiskLevel.RENDAH


def test_penjelasan_aturan_diurutkan_dari_poin_terbesar():
    hasil = _aturan(saturasi=Decimal("94"), nadi=130, td_sistolik=190)
    assert [f.kontribusi for f in hasil.penjelasan] == [3, 2, 1]


def test_skor_maksimum_aturan():
    fitur = replace(
        NORMAL,
        saturasi=Decimal("80"),
        td_sistolik=200,
        nadi=150,
        suhu=Decimal("40"),
        laju_napas=35,
        gejala="nyeri dada hebat",
        tingkat_kesadaran=TingkatKesadaran.TIDAK_RESPONS,
    )
    assert sum(f.kontribusi for f in RuleBasedClassifier.aturan_terpicu(fitur)) == SKOR_MAKSIMUM_ATURAN


# ---------------------------------------------------------------- FallbackClassifier


class _ClassifierRusak:
    def klasifikasi(self, fitur):
        raise RuntimeError("model rusak")


def test_fallback_memakai_aturan_bila_model_error(caplog):
    hasil = FallbackClassifier(utama=_ClassifierRusak(), cadangan=RuleBasedClassifier(AMBANG)).klasifikasi(NORMAL)
    assert hasil.sumber == SumberRekomendasi.ATURAN
    assert "memakai aturan cadangan" in caplog.text


def test_fallback_memakai_aturan_bila_model_tidak_ada():
    hasil = buat_klasifikator(None, AMBANG).klasifikasi(NORMAL)
    assert hasil.sumber == SumberRekomendasi.ATURAN


def test_fallback_memakai_model_bila_tersedia(model):
    assert buat_klasifikator(model, AMBANG).klasifikasi(NORMAL).sumber == SumberRekomendasi.MODEL


# ---------------------------------------------------------------- label dan format


@pytest.mark.parametrize(
    ("nama", "nilai", "label"),
    [
        ("Saturation", 88.0, "Saturasi oksigen 88%"),
        ("BT", 37.5, "Suhu tubuh 37,5 °C"),
        ("SBP", 168, "Tekanan darah sistolik 168 mmHg"),
        ("DBP", 102, "Tekanan darah diastolik 102 mmHg"),
        ("HR", 118, "Nadi 118 x/menit"),
        ("RR", 28, "Laju napas 28 x/menit"),
        ("NRS_pain", 7, "Skala nyeri 7"),
        ("Age", 45, "Usia 45 tahun"),
        ("Sex", "laki_laki", "Jenis kelamin laki-laki"),
        ("Mental", "P", "Tingkat kesadaran P (respons terhadap nyeri)"),
        ("kategori_keluhan", "Nyeri dada", "Kategori keluhan: Nyeri dada"),
        ("map", 124.33, "Tekanan arteri rata-rata 124,3 mmHg"),
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


def test_dari_shap_membuang_kategori_bernilai_nol():
    nama = ("kategori__kategori_keluhan_Demam", "kategori__kategori_keluhan_Pusing", "angka__HR")
    faktor = PenyusunPenjelasan.dari_shap([0.9, 0.2, -0.1], nama, [0, 1, 80], {"HR": 80})
    assert [f.label for f in faktor] == ["Kategori keluhan: Pusing", "Nadi 80 x/menit"]
    assert [f.arah for f in faktor] == ["naik", "turun"]


def test_faktor_ke_json():
    assert Faktor("HR", "Nadi 80 x/menit", 80, 0.1, "naik").ke_json() == {
        "fitur": "HR",
        "label": "Nadi 80 x/menit",
        "nilai": 80,
        "kontribusi": 0.1,
        "arah": "naik",
    }
