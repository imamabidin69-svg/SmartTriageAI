"""Mengukur persentase angka terbaca benar pada set foto uji (target >= 95%, Desain 7.3 dan NFR-04).

Evaluasi memakai PembacaLayarOnnx, PenyusunAngka, dan PemetaKolom yang sama dengan backend, jadi angkanya
mencerminkan perilaku produksi. Ambang keyakinan tidak diterapkan di sini, karena yang diukur adalah
ketepatan pembacaan; kolom yang tidak terbaca dihitung salah.

Berkas label (CSV berpemisah titik koma) berisi kolom: berkas;jenis_alat;nilai
contoh: tensi_001.jpg;tensimeter;td_sistolik=128,td_diastolik=84,nadi=76

Contoh: python -m ai_training.evaluasi --model yolo_digit.onnx --foto /content/uji --label /content/uji/label.csv
"""

import argparse
import csv
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from PIL import Image, ImageOps

from app.ai.pembaca_layar import PembacaLayar, PembacaLayarOnnx
from app.ai.penyusun_angka import PemetaKolom, PenyusunAngka
from app.models.enums import JenisAlat

TARGET_AKURASI = 95.0


@dataclass(frozen=True)
class Label:
    berkas: str
    jenis_alat: JenisAlat
    nilai: dict[str, Decimal]


@dataclass(frozen=True)
class HasilEvaluasi:
    total_kolom: int
    kolom_benar: int
    salah: list[str]

    @property
    def akurasi(self) -> float:
        return round(self.kolom_benar / self.total_kolom * 100, 1) if self.total_kolom else 0.0

    @property
    def lulus(self) -> bool:
        return self.akurasi >= TARGET_AKURASI


def baca_label(path: Path) -> list[Label]:
    hasil = []
    with Path(path).open(encoding="utf-8-sig", newline="") as berkas:
        for nomor, baris in enumerate(csv.DictReader(berkas, delimiter=";"), start=2):
            try:
                pasangan = (bagian.split("=") for bagian in baris["nilai"].split(","))
                nilai = {kolom.strip(): Decimal(angka.strip()) for kolom, angka in pasangan}
                hasil.append(Label(baris["berkas"].strip(), JenisAlat(baris["jenis_alat"].strip()), nilai))
            except (KeyError, ValueError, ArithmeticError) as galat:
                raise ValueError(f"Baris {nomor} berkas label tidak valid: {dict(baris)}") from galat
    return hasil


def evaluasi(pembaca: PembacaLayar, folder_foto: Path, label: list[Label]) -> HasilEvaluasi:
    penyusun, pemeta = PenyusunAngka(), PemetaKolom()
    total = benar = 0
    salah = []
    for item in label:
        with Image.open(Path(folder_foto) / item.berkas) as foto:
            gambar = ImageOps.exif_transpose(foto).convert("RGB")
        gambar.thumbnail((640, 640))
        terbaca = pemeta.petakan(penyusun.susun(pembaca.deteksi(gambar, item.jenis_alat)), item.jenis_alat)
        for kolom, harapan in item.nilai.items():
            total += 1
            didapat = terbaca.get(kolom)
            if didapat is not None and Decimal(didapat.nilai) == harapan:
                benar += 1
            else:
                salah.append(f"{item.berkas} {kolom}: harapan {harapan}, terbaca {didapat.nilai if didapat else '-'}")
    return HasilEvaluasi(total, benar, salah)


def main(daftar: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluasi pembaca layar pada set foto uji.")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--foto", type=Path, required=True)
    parser.add_argument("--label", type=Path, required=True)
    a = parser.parse_args(daftar)

    hasil = evaluasi(PembacaLayarOnnx(str(a.model)), a.foto, baca_label(a.label))
    for baris in hasil.salah:
        print("SALAH", baris)
    status = "LULUS" if hasil.lulus else "BELUM LULUS"
    print(f"Akurasi {hasil.akurasi}% ({hasil.kolom_benar}/{hasil.total_kolom}), target {TARGET_AKURASI}%: {status}")
    return 0 if hasil.lulus else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
