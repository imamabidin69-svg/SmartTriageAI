"""Melatih YOLO versi nano untuk mendeteksi digit 0-9 di Google Colab.

Contoh: python -m ai_training.latih --data /content/dataset/data.yaml --epoch 100

Bobot awal memakai yolo11n.pt. Generasi YOLO yang lebih baru (misalnya YOLO26) mengekspor ONNX tanpa
NMS dengan bentuk keluaran berbeda, sehingga tidak cocok dengan dekoder di app/ai/pembaca_layar.py.
"""

import argparse
from pathlib import Path

BOBOT_AWAL = "yolo11n.pt"
UKURAN_GAMBAR = 640


def argumen(daftar: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Latih detektor digit layar alat.")
    parser.add_argument("--data", type=Path, required=True, help="Path data.yaml dari ai_training.dataset.")
    parser.add_argument("--epoch", type=int, default=100)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--nama", default="digit_layar", help="Nama folder hasil di runs/detect/.")
    return parser.parse_args(daftar)


def latih(data: Path, epoch: int, batch: int, nama: str) -> Path:  # pragma: no cover
    from ultralytics import YOLO

    model = YOLO(BOBOT_AWAL)
    # Augmentasi warna dan sudut membantu karena foto diambil di berbagai pencahayaan; flip dimatikan
    # karena digit yang dicerminkan (misalnya 2 dan 5) bisa tertukar.
    hasil = model.train(
        data=str(data), epochs=epoch, batch=batch, imgsz=UKURAN_GAMBAR, name=nama, fliplr=0.0, degrees=8.0
    )
    return Path(hasil.save_dir) / "weights" / "best.pt"


if __name__ == "__main__":  # pragma: no cover
    a = argumen()
    print(f"Bobot terbaik: {latih(a.data, a.epoch, a.batch, a.nama)}")
