"""Membuat model ONNX kecil berbentuk detektor YOLO untuk menguji PembacaLayarOnnx tanpa model asli."""

from pathlib import Path

import numpy as np
import onnx
from onnx import TensorProto, helper, numpy_helper


def kotak_yolo(digit: list[tuple[int, float, float, float, float, float]], jumlah_kotak: int = 32) -> np.ndarray:
    """Tensor keluaran (1, 14, N). Setiap digit: (kelas, skor, cx, cy, w, h); sisa kotak berskor nol."""
    keluaran = np.zeros((1, 14, jumlah_kotak), dtype=np.float32)
    for i, (kelas, skor, cx, cy, w, h) in enumerate(digit):
        keluaran[0, :4, i] = (cx, cy, w, h)
        keluaran[0, 4 + kelas, i] = skor
    return keluaran


def buat_model(path: Path, keluaran: np.ndarray, ukuran_masukan: int = 640) -> Path:
    """Model yang selalu mengembalikan `keluaran` apa pun gambarnya.

    Masukan tetap dipakai (dikalikan nol lalu dijumlahkan) supaya bentuk tensor masukan ikut diperiksa runtime.
    """
    nol = numpy_helper.from_array(np.zeros((1,), dtype=np.float32), "nol")
    tetap = numpy_helper.from_array(keluaran.astype(np.float32), "tetap")
    simpul = [
        helper.make_node("ReduceSum", ["images"], ["jumlah"], keepdims=0),
        helper.make_node("Mul", ["jumlah", "nol"], ["nol_kali"]),
        helper.make_node("Add", ["tetap", "nol_kali"], ["output0"]),
    ]
    graf = helper.make_graph(
        simpul,
        "detektor_digit_tiruan",
        [helper.make_tensor_value_info("images", TensorProto.FLOAT, [1, 3, ukuran_masukan, ukuran_masukan])],
        [helper.make_tensor_value_info("output0", TensorProto.FLOAT, list(keluaran.shape))],
        [nol, tetap],
    )
    model = helper.make_model(graf, opset_imports=[helper.make_opsetid("", 13)])
    model.ir_version = 8
    onnx.save(model, str(path))
    return path
