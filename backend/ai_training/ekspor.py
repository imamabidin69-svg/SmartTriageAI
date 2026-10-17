"""Mengekspor bobot hasil pelatihan ke ONNX lalu memastikan formatnya cocok dengan backend.

Contoh: python -m ai_training.ekspor --bobot runs/detect/digit_layar/weights/best.pt
Hasilnya disalin ke backend/app/ai/artefak/yolo_digit.onnx (atau path di MODEL_YOLO_PATH).
"""

import argparse
from pathlib import Path

import numpy as np

UKURAN_GAMBAR = 640


def periksa_onnx(path: Path) -> tuple[int, ...]:
    """Memuat model dengan PembacaLayarOnnx dan memastikan keluarannya berbentuk (1, 14, N).

    Mengembalikan bentuk keluaran supaya bisa dicatat di laporan pelatihan.
    """
    from app.ai.pembaca_layar import JUMLAH_KELAS, ModelPembacaTidakSesuaiError, PembacaLayarOnnx

    pembaca = PembacaLayarOnnx(str(path))
    kosong = np.zeros((1, 3, UKURAN_GAMBAR, UKURAN_GAMBAR), dtype=np.float32)
    bentuk = tuple(np.asarray(pembaca.sesi.run(None, {pembaca.nama_masukan: kosong})[0]).shape)
    if len(bentuk) != 3 or bentuk[0] != 1 or bentuk[1] != 4 + JUMLAH_KELAS:
        raise ModelPembacaTidakSesuaiError(f"Keluaran model {bentuk} bukan (1, {4 + JUMLAH_KELAS}, N).")
    return bentuk


def ekspor(bobot: Path) -> Path:  # pragma: no cover
    from ultralytics import YOLO

    # Ukuran tetap 640, tanpa NMS di dalam model (NMS dikerjakan backend), opset yang didukung onnxruntime.
    hasil = YOLO(str(bobot)).export(format="onnx", imgsz=UKURAN_GAMBAR, dynamic=False, simplify=True, opset=12)
    return Path(hasil)


if __name__ == "__main__":  # pragma: no cover
    parser = argparse.ArgumentParser(description="Ekspor bobot YOLO ke ONNX.")
    parser.add_argument("--bobot", type=Path, required=True)
    path = ekspor(parser.parse_args().bobot)
    print(f"Model ONNX: {path}, bentuk keluaran {periksa_onnx(path)}")
