"""Bagian skrip pelatihan YOLO yang bisa diuji tanpa GPU dan ultralytics (keputusan P7)."""

from decimal import Decimal
from pathlib import Path

import numpy as np
import pytest
from bantuan_onnx import buat_model, kotak_yolo
from PIL import Image

from ai_training import ekspor, evaluasi, latih
from ai_training.dataset import NAMA_KELAS, DatasetTidakSesuaiError, periksa_kelas, tulis_data_yaml
from app.ai.pembaca_layar import ModelPembacaTidakSesuaiError, PembacaLayarTiruan
from app.models.enums import JenisAlat

# ---------------------------------------------------------------- dataset


def test_kelas_harus_digit_0_sampai_9_berurutan():
    periksa_kelas(NAMA_KELAS)
    with pytest.raises(DatasetTidakSesuaiError):
        periksa_kelas(["1", "0", "2", "3", "4", "5", "6", "7", "8", "9"])
    with pytest.raises(DatasetTidakSesuaiError):
        periksa_kelas([*NAMA_KELAS, "titik"])


def test_tulis_data_yaml(tmp_path):
    for bagian in ("train", "valid", "test"):
        (tmp_path / bagian / "images").mkdir(parents=True)
    isi = tulis_data_yaml(tmp_path).read_text()
    assert f"path: {tmp_path.resolve()}" in isi
    assert "val: valid/images" in isi
    assert "nc: 10" in isi
    assert "names: ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']" in isi


def test_data_yaml_menolak_folder_tidak_lengkap(tmp_path):
    (tmp_path / "train" / "images").mkdir(parents=True)
    with pytest.raises(DatasetTidakSesuaiError, match="valid"):
        tulis_data_yaml(tmp_path)


def test_argumen_latih(tmp_path):
    a = latih.argumen(["--data", str(tmp_path / "data.yaml"), "--epoch", "5"])
    assert (a.epoch, a.batch, a.nama) == (5, 16, "digit_layar")
    assert latih.BOBOT_AWAL == "yolo11n.pt"


# ---------------------------------------------------------------- ekspor


def test_periksa_onnx_menerima_model_yang_cocok(tmp_path):
    path = buat_model(tmp_path / "digit.onnx", kotak_yolo([], jumlah_kotak=8400))
    assert ekspor.periksa_onnx(path) == (1, 14, 8400)


def test_periksa_onnx_menolak_jumlah_kelas_lain(tmp_path):
    path = buat_model(tmp_path / "coco.onnx", np.zeros((1, 84, 8), dtype=np.float32))
    with pytest.raises(ModelPembacaTidakSesuaiError):
        ekspor.periksa_onnx(path)


# ---------------------------------------------------------------- evaluasi


def _label(tmp_path, isi: str):
    path = tmp_path / "label.csv"
    path.write_text("﻿berkas;jenis_alat;nilai\n" + isi, encoding="utf-8")
    return path


def test_baca_label(tmp_path):
    [label] = evaluasi.baca_label(_label(tmp_path, "termo_1.jpg;termometer;suhu=36.8\n"))
    assert (label.berkas, label.jenis_alat, label.nilai) == (
        "termo_1.jpg",
        JenisAlat.TERMOMETER,
        {"suhu": Decimal("36.8")},
    )


@pytest.mark.parametrize("baris", ["a.jpg;timbangan;nadi=80", "a.jpg;oksimeter;nadi", "a.jpg;oksimeter;nadi=abc"])
def test_label_tidak_valid(tmp_path, baris):
    with pytest.raises(ValueError, match="Baris 2"):
        evaluasi.baca_label(_label(tmp_path, baris + "\n"))


def _foto(folder, nama):
    Image.new("RGB", (800, 600)).save(folder / nama)


def test_evaluasi_menghitung_kolom_benar(tmp_path):
    _foto(tmp_path, "tensi.jpg")
    _foto(tmp_path, "oksi.jpg")
    label = evaluasi.baca_label(
        _label(
            tmp_path,
            "tensi.jpg;tensimeter;td_sistolik=128,td_diastolik=84,nadi=76\noksi.jpg;oksimeter;saturasi=97,nadi=80\n",
        )
    )
    hasil = evaluasi.evaluasi(PembacaLayarTiruan(), tmp_path, label)
    # Pembaca tiruan membaca oksimeter 97 dan 82, jadi nadi oksimeter salah: 4 dari 5.
    assert (hasil.kolom_benar, hasil.total_kolom, hasil.akurasi, hasil.lulus) == (4, 5, 80.0, False)
    assert hasil.salah == ["oksi.jpg nadi: harapan 80, terbaca 82"]


def test_kolom_tidak_terbaca_dihitung_salah(tmp_path):
    _foto(tmp_path, "monitor.jpg")
    label = evaluasi.baca_label(_label(tmp_path, "monitor.jpg;bedside_monitor;nadi=80\n"))
    hasil = evaluasi.evaluasi(PembacaLayarTiruan(), tmp_path, label)
    assert hasil.salah == ["monitor.jpg nadi: harapan 80, terbaca -"]


def test_akurasi_tanpa_kolom():
    assert evaluasi.HasilEvaluasi(0, 0, []).akurasi == 0.0


def _model_tensimeter(path):
    # Tiga baris digit "128", "84", "76" dalam koordinat masukan model 640x640.
    digit = []
    for y, teks in ((100, "128"), (220, "84"), (340, "76")):
        digit += [(int(c), 0.95, 100 + i * 50, y, 40, 80) for i, c in enumerate(teks)]
    return buat_model(path, kotak_yolo(digit))


@pytest.mark.parametrize(("nadi", "kode", "teks"), [(76, 0, "LULUS"), (90, 1, "BELUM LULUS")])
def test_main_evaluasi(tmp_path, capsys, nadi, kode, teks):
    model = _model_tensimeter(tmp_path / "digit.onnx")
    _foto(tmp_path, "tensi.jpg")
    label = _label(tmp_path, f"tensi.jpg;tensimeter;td_sistolik=128,td_diastolik=84,nadi={nadi}\n")
    hasil = evaluasi.main(["--model", str(model), "--foto", str(tmp_path), "--label", str(label)])
    assert hasil == kode
    assert f": {teks}" in capsys.readouterr().out


# ---------------------------------------------------------------- model perburukan ICU (PhysioNet 2019)

KOLOM_PSV = [
    "HR",
    "O2Sat",
    "Temp",
    "SBP",
    "MAP",
    "DBP",
    "Resp",
    "EtCO2",
    "BaseExcess",
    "HCO3",
    "FiO2",
    "pH",
    "PaCO2",
    "SaO2",
    "AST",
    "BUN",
    "Alkalinephos",
    "Calcium",
    "Chloride",
    "Creatinine",
    "Bilirubin_direct",
    "Glucose",
    "Lactate",
    "Magnesium",
    "Phosphate",
    "Potassium",
    "Bilirubin_total",
    "TroponinI",
    "Hct",
    "Hgb",
    "PTT",
    "WBC",
    "Fibrinogen",
    "Platelets",
    "Age",
    "Gender",
    "Unit1",
    "Unit2",
    "HospAdmTime",
    "ICULOS",
    "SepsisLabel",
]


def _tulis_pasien(folder, nomor, memburuk, jam=12, seed=0):
    """Satu berkas .psv sintetis: pasien yang memburuk punya nadi, napas, suhu, dan laktat yang naik."""
    acak = np.random.default_rng(seed + nomor)
    baris = ["|".join(KOLOM_PSV)]
    for t in range(jam):
        label = int(memburuk and t >= jam // 2)
        nilai = dict.fromkeys(KOLOM_PSV, "NaN")
        nilai.update(
            HR=f"{(120 if label else 80) + acak.normal(0, 5):.0f}",
            O2Sat=f"{(91 if label else 98) + acak.normal(0, 1):.0f}",
            Temp=f"{(38.9 if label else 36.8) + acak.normal(0, 0.2):.1f}" if t % 2 == 0 else "NaN",
            SBP=f"{(92 if label else 125) + acak.normal(0, 5):.0f}",
            DBP=f"{(50 if label else 78) + acak.normal(0, 4):.0f}",
            Resp=f"{(26 if label else 16) + acak.normal(0, 2):.0f}",
            Age="60",
            Gender=str(nomor % 2),
            ICULOS=str(t + 1),
            SepsisLabel=str(label),
        )
        if t == 0:
            nilai["MAP"] = "90"
            nilai.update(HR="NaN", O2Sat="NaN", SBP="NaN", DBP="NaN", Resp="NaN")
        if t == 3:
            nilai["Lactate"] = "4.5" if memburuk else "1.1"
        baris.append("|".join(nilai[k] for k in KOLOM_PSV))
    path = folder / f"p{nomor:06d}.psv"
    path.write_text("\n".join(baris) + "\n", encoding="utf-8")
    return path


@pytest.fixture
def data_physionet(tmp_path):
    folder = tmp_path / "physionet"
    folder.mkdir()
    for nomor in range(1, 41):
        _tulis_pasien(folder, nomor, memburuk=nomor % 3 == 0)
    return folder


def test_fitur_dari_physionet_forward_fill_dan_turunan(data_physionet):
    import pandas as pd

    from ai_training import perburukan

    fitur = perburukan.fitur_dari_physionet(pd.read_csv(data_physionet / "p000003.psv", sep="|"))
    # Jam pertama tanpa tanda vital dibuang.
    assert len(fitur) == 11
    assert list(fitur.columns) == [*perburukan.FITUR_MODEL, "label"]
    # Suhu hanya diukur tiap dua jam dan laktat sekali, lalu dibawa ke jam berikutnya.
    assert fitur["suhu"].notna().all()
    assert (fitur["laktat"].iloc[2:] == 4.5).all()
    assert fitur["shock_index"].iloc[0] == pytest.approx(fitur["nadi"].iloc[0] / fitur["td_sistolik"].iloc[0])
    assert set(fitur["label"]) == {0, 1}


def test_fitur_physionet_menolak_kolom_kurang():
    import pandas as pd

    from ai_training import perburukan

    with pytest.raises(perburukan.DataTidakSesuaiError, match="SepsisLabel"):
        perburukan.fitur_dari_physionet(pd.DataFrame({"HR": [80]}))


def test_bagi_pasien_tidak_tumpang_tindih(data_physionet):
    from ai_training import perburukan

    berkas = sorted(data_physionet.glob("*.psv"))
    latih, uji = perburukan.bagi_pasien(berkas, 0.25, 7)
    assert len(uji) == 10
    assert set(latih).isdisjoint(uji)
    assert sorted(latih + uji) == berkas


def test_pilih_ambang_dan_level_dari_peluang():
    from ai_training import perburukan

    ambang = perburukan.pilih_ambang(np.linspace(0, 1, 101))
    assert ambang == {"sedang": 0.7, "tinggi": 0.9, "kritis": 0.97}
    level = perburukan.level_dari_peluang(np.array([0.1, 0.75, 0.95, 0.99]), ambang)
    assert level.tolist() == [0, 1, 2, 3]


def test_latih_dan_simpan_bundle_yang_dibaca_registry(data_physionet, tmp_path):
    from ai_training import perburukan
    from app.ai.registry import ModelRegistry

    param = perburukan.Parameter(pohon=20, kedalaman=4, daun_minimum=2, rasio_negatif=1.0, porsi_uji=0.25)
    hasil = perburukan.latih(data_physionet, param)
    laporan = hasil["laporan"]
    assert laporan["jumlah_pasien"] == {"latih": 30, "uji": 10}
    assert laporan["uji"]["auroc"] > 0.9
    assert set(laporan["uji"]["per_level"]) == {"rendah", "sedang", "tinggi", "kritis"}
    assert set(laporan["pentingnya_fitur"]) == set(perburukan.FITUR_MODEL)

    keluaran = tmp_path / "model.joblib"
    perburukan.simpan(hasil, keluaran, tmp_path / "laporan.json")
    assert (tmp_path / "laporan.json").read_text(encoding="utf-8").startswith("{")
    registry = ModelRegistry()
    registry.muat(str(keluaran))
    assert registry.termuat
    assert registry.versi_model == perburukan.VERSI


def test_latih_menolak_data_yang_terlalu_sedikit(data_physionet, tmp_path):
    from ai_training import perburukan

    with pytest.raises(perburukan.DataTidakSesuaiError, match="kurang dari dua"):
        perburukan.latih(data_physionet, perburukan.Parameter(), batas_pasien=1)
    kosong = tmp_path / "semua_stabil"
    kosong.mkdir()
    for nomor in range(1, 5):
        _tulis_pasien(kosong, nomor, memburuk=False)
    with pytest.raises(perburukan.DataTidakSesuaiError, match="label 0 dan 1"):
        perburukan.latih(kosong, perburukan.Parameter(pohon=5, porsi_uji=0.25))


def test_evaluasi_tanpa_label_positif():
    from ai_training import perburukan

    y = np.array([0, 1, 0, 1])
    hasil = perburukan.evaluasi(y, np.array([0.1, 0.9, 0.2, 0.8]), {"sedang": 0.5, "tinggi": 0.85, "kritis": 0.95})
    assert hasil["auroc"] == 1.0
    assert hasil["per_level"]["kritis"] == {"jumlah_jam": 0, "persen_berlabel_1": None}
    assert hasil["sensitivitas_persen"] == {"minimal_sedang": 100.0, "minimal_tinggi": 50.0, "minimal_kritis": 0.0}


def test_argumen_perburukan():
    from ai_training import perburukan

    a = perburukan.argumen(["--data", "/data"])
    assert (a.data, a.proses, a.batas_pasien) == (Path("/data"), 4, None)


# ---------------------------------------------------------------- dataset Roboflow Universe dengan nama kelas lain


@pytest.mark.parametrize(
    ("nama", "digit"),
    [("7", 7), ("digit_7", 7), ("num-3", 3), ("Seven", 7), ("nol", 0), ("HR", None), ("spo2", None), ("17", None)],
)
def test_digit_dari_nama(nama, digit):
    from ai_training.dataset import digit_dari_nama

    assert digit_dari_nama(nama) == digit


def test_peta_kelas_dan_tulis_ulang_label(tmp_path):
    from ai_training.dataset import peta_kelas_digit, tulis_ulang_label

    kelas = ["HR", *[f"digit_{i}" for i in range(9, -1, -1)], "spo2"]
    peta = peta_kelas_digit(kelas)
    assert peta[1] == 9
    assert peta[10] == 0
    assert 0 not in peta
    label = tmp_path / "train" / "labels"
    label.mkdir(parents=True)
    (label / "a.txt").write_text("0 0.5 0.5 0.2 0.2\n1 0.1 0.1 0.05 0.05\n10 0.2 0.2 0.05 0.05\n\n", encoding="utf-8")
    (label / "b.txt").write_text("11 0.5 0.5 0.2 0.2\n", encoding="utf-8")
    assert tulis_ulang_label(tmp_path, peta) == 2
    assert (label / "a.txt").read_text(encoding="utf-8") == "9 0.1 0.1 0.05 0.05\n0 0.2 0.2 0.05 0.05\n"
    assert (label / "b.txt").read_text(encoding="utf-8") == ""


def test_peta_kelas_menolak_dataset_tanpa_semua_digit():
    from ai_training.dataset import peta_kelas_digit

    with pytest.raises(DatasetTidakSesuaiError, match=r"\[8, 9\]"):
        peta_kelas_digit([str(i) for i in range(8)] + ["HR"])


# ---------------------------------------------------------------- menggabungkan beberapa dataset Roboflow


@pytest.mark.parametrize(
    ("isi", "nama"),
    [
        ("nc: 3\nnames: ['-', '.', '0']\n", ["-", ".", "0"]),
        ("names:\n  0: Health_Monitor\n  1: 'digit'\nroboflow:\n  versi: 1\n", ["Health_Monitor", "digit"]),
        ("names:\n- '0'\n- \"1\"\n\nnc: 2\n", ["0", "1"]),
    ],
)
def test_baca_nama_kelas(tmp_path, isi, nama):
    from ai_training.dataset import baca_nama_kelas

    (tmp_path / "data.yaml").write_text(isi, encoding="utf-8")
    assert baca_nama_kelas(tmp_path / "data.yaml") == nama


def test_baca_nama_kelas_tanpa_names(tmp_path):
    from ai_training.dataset import baca_nama_kelas

    (tmp_path / "data.yaml").write_text("nc: 2\n", encoding="utf-8")
    with pytest.raises(DatasetTidakSesuaiError, match="names"):
        baca_nama_kelas(tmp_path / "data.yaml")


def _dataset_roboflow(folder: Path, kelas: list[str], label: dict[str, dict[str, str]]) -> Path:
    (folder).mkdir(parents=True)
    (folder / "data.yaml").write_text(f"nc: {len(kelas)}\nnames: {kelas!r}\n", encoding="utf-8")
    for bagian, berkas in label.items():
        (folder / bagian / "images").mkdir(parents=True)
        (folder / bagian / "labels").mkdir(parents=True)
        for nama, isi in berkas.items():
            Image.new("RGB", (8, 8)).save(folder / bagian / "images" / f"{nama}.JPG")
            if isi is not None:
                (folder / bagian / "labels" / f"{nama}.txt").write_text(isi, encoding="utf-8")
    return folder


def test_gabung_dataset(tmp_path):
    from ai_training.dataset import gabung_dataset

    # Dataset pertama memakai urutan kelas Roboflow ('-', '.', '0'-'9') dan satu label poligon.
    a = _dataset_roboflow(
        tmp_path / "a",
        ["-", ".", *[str(i) for i in range(10)]],
        {
            "train": {"x": "2 0.5 0.5 0.2 0.4\n0 0.1 0.1 0.1 0.1\n11 0.1 0.2 0.3 0.2 0.3 0.4 0.1 0.4\n"},
            "valid": {"y": "1 0.5 0.5 0.1 0.1\n"},
        },
    )
    # Dataset kedua memakai nama kelas "10" yang bukan digit, foto tanpa berkas label, dan kotak berukuran nol.
    b = _dataset_roboflow(
        tmp_path / "b",
        ["0", "1", "10", *[str(i) for i in range(2, 10)]],
        {"train": {"x": "3 0.5 0.5 0.2 0.2\n2 0.5 0.5 0.9 0.9\n4 0.5 0.5 0 0.2\n"}, "test": {"z": None}},
    )
    tujuan = tmp_path / "gabungan"
    (tujuan / "lama").mkdir(parents=True)

    statistik = gabung_dataset([a, b], tujuan)

    assert statistik == {"a": {"foto": 2, "kotak": 2}, "b": {"foto": 2, "kotak": 1}}
    assert not (tujuan / "lama").exists()
    assert sorted(p.name for p in (tujuan / "train" / "images").iterdir()) == ["d0_x.jpg", "d1_x.jpg"]
    assert (tujuan / "train" / "labels" / "d0_x.txt").read_text() == (
        "0 0.500000 0.500000 0.200000 0.400000\n9 0.200000 0.300000 0.200000 0.200000\n"
    )
    assert (tujuan / "train" / "labels" / "d1_x.txt").read_text() == "2 0.500000 0.500000 0.200000 0.200000\n"
    assert (tujuan / "valid" / "labels" / "d0_y.txt").read_text() == ""
    assert (tujuan / "test" / "labels" / "d1_z.txt").read_text() == ""
    assert "names: ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']" in (tujuan / "data.yaml").read_text()


def test_gabung_dataset_menolak_dataset_tanpa_digit(tmp_path):
    from ai_training.dataset import gabung_dataset

    a = _dataset_roboflow(tmp_path / "a", ["Health_Monitor"], {"train": {"x": "0 0.5 0.5 0.2 0.2\n"}})
    with pytest.raises(DatasetTidakSesuaiError):
        gabung_dataset([a], tmp_path / "gabungan")
