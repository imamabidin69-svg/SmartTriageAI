"""PembacaLayarOnnx dan PembacaLayarTiruan (FR-04, Desain 2.4 dan 7.3).

Model YOLO asli belum ada, jadi jalur ONNX diuji dengan model kecil yang selalu mengembalikan kotak
tertentu (lihat bantuan_onnx.py).
"""

import numpy as np
import pytest
from bantuan_onnx import buat_model, kotak_yolo
from PIL import Image

from app.ai.pembaca_layar import (
    CONTOH_TIRUAN,
    Digit,
    ModelPembacaTidakSesuaiError,
    PembacaLayarOnnx,
    PembacaLayarTiruan,
    dekode_keluaran,
    letterbox,
    nms,
)
from app.ai.registry import ModelRegistry
from app.models.enums import JenisAlat


def test_letterbox_menjaga_rasio_dan_memberi_bantalan():
    gambar = Image.new("RGB", (320, 160), (255, 0, 0))
    tensor = letterbox(gambar)
    assert tensor.shape == (1, 3, 640, 640)
    assert tensor.dtype == np.float32
    # Bagian atas berisi gambar (merah), bagian bawah bantalan abu-abu 114.
    assert tensor[0, :, 10, 10].tolist() == pytest.approx([1.0, 0.0, 0.0])
    assert tensor[0, :, 600, 10].tolist() == pytest.approx([114 / 255] * 3)


def test_nms_membuang_kotak_yang_bertumpuk():
    kotak = np.array([[0, 0, 10, 10], [1, 1, 11, 11], [50, 50, 60, 60]], dtype=np.float32)
    skor = np.array([0.8, 0.9, 0.7], dtype=np.float32)
    assert nms(kotak, skor) == [1, 2]


def test_nms_kotak_berukuran_nol_tidak_saling_membuang():
    kotak = np.array([[5, 5, 5, 5], [5, 5, 5, 5]], dtype=np.float32)
    assert nms(kotak, np.array([0.9, 0.8], dtype=np.float32)) == [0, 1]


def test_dekode_keluaran_memilih_kelas_dan_menyaring_skor_rendah():
    keluaran = kotak_yolo([(7, 0.9, 100, 100, 40, 80), (3, 0.1, 300, 100, 40, 80)])
    [digit] = dekode_keluaran(keluaran)
    assert (digit.nilai, round(digit.keyakinan, 2)) == (7, 0.9)
    assert (digit.x1, digit.y1, digit.x2, digit.y2) == (80, 60, 120, 140)


def test_dekode_tanpa_deteksi():
    assert dekode_keluaran(kotak_yolo([])) == []


@pytest.mark.parametrize("bentuk", [(1, 15, 8), (14, 8), (2, 14, 8)])
def test_dekode_menolak_bentuk_keluaran_asing(bentuk):
    with pytest.raises(ModelPembacaTidakSesuaiError):
        dekode_keluaran(np.zeros(bentuk, dtype=np.float32))


def test_pembaca_onnx_membaca_digit(tmp_path):
    keluaran = kotak_yolo([(1, 0.9, 100, 100, 40, 80), (2, 0.95, 150, 100, 40, 80), (2, 0.5, 152, 101, 40, 80)])
    pembaca = PembacaLayarOnnx(str(buat_model(tmp_path / "digit.onnx", keluaran)))
    digit = pembaca.deteksi(Image.new("RGB", (300, 200)), JenisAlat.TENSIMETER)
    assert sorted(d.nilai for d in digit) == [1, 2]


def test_pembaca_onnx_menolak_ukuran_masukan_lain(tmp_path):
    path = buat_model(tmp_path / "kecil.onnx", kotak_yolo([]), ukuran_masukan=320)
    with pytest.raises(ModelPembacaTidakSesuaiError):
        PembacaLayarOnnx(str(path))


def test_pembaca_tiruan_mengembalikan_contoh_per_alat():
    pembaca = PembacaLayarTiruan()
    digit = pembaca.deteksi(Image.new("RGB", (10, 10)), JenisAlat.OKSIMETER)
    assert "".join(str(d.nilai) for d in digit) == "".join(CONTOH_TIRUAN[JenisAlat.OKSIMETER])


def test_pembaca_tiruan_dengan_digit_sendiri():
    digit = [Digit(5, 0.5, 0, 0, 10, 10)]
    pembaca = PembacaLayarTiruan({JenisAlat.TERMOMETER: digit})
    assert pembaca.deteksi(Image.new("RGB", (10, 10)), JenisAlat.TERMOMETER) == digit
    assert pembaca.deteksi(Image.new("RGB", (10, 10)), JenisAlat.OKSIMETER) == []


# ---------------------------------------------------------------- ModelRegistry


def test_registry_memuat_model_onnx(tmp_path):
    registry = ModelRegistry()
    registry.muat_pembaca_layar(str(buat_model(tmp_path / "digit.onnx", kotak_yolo([]))))
    assert isinstance(registry.pembaca_layar, PembacaLayarOnnx)


def test_registry_mode_tiruan():
    registry = ModelRegistry()
    registry.muat_pembaca_layar(None, "tiruan")
    assert isinstance(registry.pembaca_layar, PembacaLayarTiruan)


@pytest.mark.parametrize("path", [None, "", "/tidak/ada/yolo.onnx"])
def test_registry_tanpa_model(path):
    registry = ModelRegistry()
    registry.muat_pembaca_layar(path)
    assert registry.pembaca_layar is None


def test_registry_model_rusak(tmp_path, caplog):
    rusak = tmp_path / "rusak.onnx"
    rusak.write_bytes(b"bukan model onnx")
    registry = ModelRegistry()
    registry.muat_pembaca_layar(str(rusak))
    assert registry.pembaca_layar is None
    assert "gagal dimuat" in caplog.text
