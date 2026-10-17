"""PembacaLayar: mendeteksi digit pada foto layar alat tanda vital (FR-04, Desain 2.4 dan 7.3).

Model YOLO versi nano dilatih di Google Colab (lihat backend/ai_training/) dengan sepuluh kelas,
yaitu digit 0 sampai 9, lalu diekspor ke ONNX. Di sini model dijalankan dengan ONNX Runtime di CPU,
sehingga image produksi tidak memerlukan PyTorch.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image

from app.models.enums import JenisAlat

logger = logging.getLogger(__name__)

UKURAN_MASUKAN = 640
JUMLAH_KELAS = 10
# Ambang mentah deteksi YOLO. Ambang keyakinan dari tabel konfigurasi diterapkan belakangan per angka.
AMBANG_DETEKSI = 0.25
AMBANG_IOU = 0.5
WARNA_BANTALAN = 114


class ModelPembacaTidakSesuaiError(ValueError):
    """Bentuk masukan atau keluaran model ONNX tidak sesuai detektor digit 0-9."""


@dataclass(frozen=True)
class Digit:
    """Satu digit terdeteksi. Koordinat kotak memakai piksel gambar masukan model."""

    nilai: int
    keyakinan: float
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def tengah_y(self) -> float:
        return (self.y1 + self.y2) / 2

    @property
    def tinggi(self) -> float:
        return self.y2 - self.y1

    @property
    def lebar(self) -> float:
        return self.x2 - self.x1


class PembacaLayar(ABC):
    nama: str

    @abstractmethod
    def deteksi(self, gambar: Image.Image, jenis_alat: JenisAlat) -> list[Digit]:
        """Mengembalikan semua digit yang terdeteksi pada gambar RGB."""


# ---------------------------------------------------------------- ONNX


def letterbox(gambar: Image.Image, ukuran: int = UKURAN_MASUKAN) -> np.ndarray:
    """Mengubah gambar menjadi tensor 1x3xUKURANxUKURAN dengan rasio tetap dan bantalan abu-abu, seperti Ultralytics."""
    skala = ukuran / max(gambar.width, gambar.height)
    lebar, tinggi = max(1, round(gambar.width * skala)), max(1, round(gambar.height * skala))
    kanvas = Image.new("RGB", (ukuran, ukuran), (WARNA_BANTALAN,) * 3)
    kanvas.paste(gambar.convert("RGB").resize((lebar, tinggi), Image.Resampling.BILINEAR), (0, 0))
    larik = np.asarray(kanvas, dtype=np.float32) / 255.0
    return larik.transpose(2, 0, 1)[np.newaxis, ...]


def nms(kotak: np.ndarray, skor: np.ndarray, ambang_iou: float = AMBANG_IOU) -> list[int]:
    """Non-maximum suppression tanpa membedakan kelas: satu posisi digit hanya boleh punya satu tebakan."""
    urutan = list(np.argsort(-skor))
    dipilih: list[int] = []
    while urutan:
        i = urutan.pop(0)
        dipilih.append(int(i))
        sisa = []
        for j in urutan:
            x1 = max(kotak[i, 0], kotak[j, 0])
            y1 = max(kotak[i, 1], kotak[j, 1])
            x2 = min(kotak[i, 2], kotak[j, 2])
            y2 = min(kotak[i, 3], kotak[j, 3])
            irisan = max(0.0, x2 - x1) * max(0.0, y2 - y1)
            luas_i = (kotak[i, 2] - kotak[i, 0]) * (kotak[i, 3] - kotak[i, 1])
            luas_j = (kotak[j, 2] - kotak[j, 0]) * (kotak[j, 3] - kotak[j, 1])
            gabungan = luas_i + luas_j - irisan
            if gabungan <= 0 or irisan / gabungan < ambang_iou:
                sisa.append(j)
        urutan = sisa
    return dipilih


def dekode_keluaran(keluaran: np.ndarray, ambang: float = AMBANG_DETEKSI) -> list[Digit]:
    """Keluaran YOLOv8/YOLO11 berbentuk (1, 4 + kelas, jumlah_kotak): cx, cy, w, h, lalu skor per kelas."""
    if keluaran.ndim != 3 or keluaran.shape[0] != 1 or keluaran.shape[1] != 4 + JUMLAH_KELAS:
        raise ModelPembacaTidakSesuaiError(f"Bentuk keluaran model {keluaran.shape} bukan (1, 14, N).")
    baris = keluaran[0].T
    skor_kelas = baris[:, 4:]
    kelas = skor_kelas.argmax(axis=1)
    skor = skor_kelas.max(axis=1)
    lolos = skor >= ambang
    if not lolos.any():
        return []
    cx, cy, w, h = (baris[lolos, i] for i in range(4))
    kotak = np.stack([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], axis=1)
    skor, kelas = skor[lolos], kelas[lolos]
    return [Digit(int(kelas[i]), float(skor[i]), *(float(v) for v in kotak[i])) for i in nms(kotak, skor)]


@lru_cache(maxsize=2)
def _sesi_onnx(path: str, waktu_ubah: float):
    import onnxruntime as ort

    del waktu_ubah  # hanya bagian kunci cache
    opsi = ort.SessionOptions()
    # Satu thread per request supaya tidak berebut CPU dengan worker Gunicorn lain.
    opsi.intra_op_num_threads = 1
    return ort.InferenceSession(path, sess_options=opsi, providers=["CPUExecutionProvider"])


class PembacaLayarOnnx(PembacaLayar):
    nama = "onnx"

    def __init__(self, path: str) -> None:
        berkas = Path(path)
        self.sesi = _sesi_onnx(str(berkas.resolve()), berkas.stat().st_mtime)
        masukan = self.sesi.get_inputs()[0]
        if list(masukan.shape[1:]) != [3, UKURAN_MASUKAN, UKURAN_MASUKAN]:
            raise ModelPembacaTidakSesuaiError(f"Bentuk masukan model {masukan.shape} bukan (1, 3, 640, 640).")
        self.nama_masukan = masukan.name

    def deteksi(self, gambar: Image.Image, jenis_alat: JenisAlat) -> list[Digit]:
        del jenis_alat  # model mendeteksi digit apa pun alatnya
        keluaran = self.sesi.run(None, {self.nama_masukan: letterbox(gambar)})[0]
        return dekode_keluaran(np.asarray(keluaran))


# ---------------------------------------------------------------- tiruan


def digit_dari_baris(baris: list[str], keyakinan: float = 0.97) -> list[Digit]:
    """Menyusun digit tiruan: setiap teks satu baris, setiap karakter satu digit selebar 40 piksel."""
    hasil = []
    for nomor_baris, teks in enumerate(baris):
        y1 = 60 + nomor_baris * 120
        for posisi, karakter in enumerate(teks):
            x1 = 80 + posisi * 50
            hasil.append(Digit(int(karakter), keyakinan, x1, y1, x1 + 40, y1 + 80))
    return hasil


# Angka contoh untuk mode tiruan di development (keputusan P5), supaya alur kamera di aplikasi bisa
# dicoba sebelum model YOLO selesai dilatih.
CONTOH_TIRUAN = {
    JenisAlat.TENSIMETER: ["128", "84", "76"],
    JenisAlat.OKSIMETER: ["97", "82"],
    JenisAlat.TERMOMETER: ["368"],
    JenisAlat.BEDSIDE_MONITOR: ["82", "97", "128", "84", "18", "368"],
}


class PembacaLayarTiruan(PembacaLayar):
    """Pembaca tanpa model untuk tes dan mode tiruan di development. Tidak pernah dipakai di production."""

    nama = "tiruan"

    def __init__(self, digit: dict[JenisAlat, list[Digit]] | None = None) -> None:
        self.digit = digit if digit is not None else {jenis: digit_dari_baris(b) for jenis, b in CONTOH_TIRUAN.items()}

    def deteksi(self, gambar: Image.Image, jenis_alat: JenisAlat) -> list[Digit]:
        del gambar
        return list(self.digit.get(jenis_alat, []))
