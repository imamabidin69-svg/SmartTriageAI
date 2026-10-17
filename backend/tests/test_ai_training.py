"""Bagian skrip pelatihan YOLO yang bisa diuji tanpa GPU dan ultralytics (keputusan P7)."""

from decimal import Decimal

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
