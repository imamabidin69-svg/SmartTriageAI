"""Menyiapkan dataset digit dari Roboflow untuk pelatihan YOLO.

Setiap digit 0 sampai 9 pada foto layar alat dianotasi sebagai kelas tersendiri (Desain 7.3). Urutan
kelas di model harus 0-9, karena backend membaca indeks kelas langsung sebagai nilai digit.
"""

import os
from pathlib import Path

NAMA_KELAS = [str(i) for i in range(10)]


class DatasetTidakSesuaiError(ValueError):
    """Kelas atau struktur dataset tidak sesuai detektor digit 0-9."""


# Nama kelas digit yang sering dipakai dataset Roboflow Universe untuk layar monitor dan seven-segment.
EJAAN_DIGIT = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "nol": 0, "satu": 1, "dua": 2, "tiga": 3, "empat": 4, "lima": 5, "enam": 6, "tujuh": 7, "delapan": 8,
    "sembilan": 9,
}  # fmt: skip


def digit_dari_nama(nama: str) -> int | None:
    """ "7", "digit_7", "num-7", atau "seven" menjadi 7. Kelas lain (misalnya "HR" atau "spo2") menjadi None."""
    rapi = nama.strip().lower()
    if rapi in EJAAN_DIGIT:
        return EJAAN_DIGIT[rapi]
    akhir = rapi.replace("-", "_").replace(" ", "_").split("_")[-1]
    if len(akhir) == 1 and akhir.isdigit() and (akhir == rapi or not rapi[0].isdigit()):
        return int(akhir)
    return None


def peta_kelas_digit(nama_kelas: list[str]) -> dict[int, int]:
    """Indeks kelas dataset ke digit 0-9. Kelas yang bukan digit tidak masuk peta dan labelnya akan dibuang."""
    peta = {i: d for i, nama in enumerate(nama_kelas) if (d := digit_dari_nama(str(nama))) is not None}
    kurang = sorted(set(range(10)) - set(peta.values()))
    if kurang:
        raise DatasetTidakSesuaiError(
            f"Dataset tidak punya kelas untuk digit {kurang}. Pilih dataset lain atau anotasi digitnya di Roboflow."
        )
    return peta


def tulis_ulang_label(folder: Path, peta: dict[int, int]) -> int:
    """Mengganti indeks kelas di semua berkas label YOLO sesuai peta, membuang baris kelas non-digit.

    Mengembalikan jumlah kotak digit yang tersisa.
    """
    jumlah = 0
    for berkas in Path(folder).glob("*/labels/*.txt"):
        baris_baru = []
        for baris in berkas.read_text(encoding="utf-8").splitlines():
            bagian = baris.split()
            if not bagian or int(bagian[0]) not in peta:
                continue
            baris_baru.append(" ".join([str(peta[int(bagian[0])]), *bagian[1:]]))
        berkas.write_text("\n".join(baris_baru) + ("\n" if baris_baru else ""), encoding="utf-8")
        jumlah += len(baris_baru)
    return jumlah


def periksa_kelas(nama_kelas: list[str]) -> None:
    if list(nama_kelas) != NAMA_KELAS:
        raise DatasetTidakSesuaiError(
            f"Kelas dataset harus tepat {NAMA_KELAS} dengan urutan yang sama, ternyata {list(nama_kelas)}."
        )


def tulis_data_yaml(folder: Path) -> Path:
    """Menulis data.yaml untuk Ultralytics dengan path absolut ke folder train, valid, dan test."""
    folder = Path(folder).resolve()
    for bagian in ("train", "valid", "test"):
        if not (folder / bagian / "images").is_dir():
            raise DatasetTidakSesuaiError(f"Folder {folder / bagian / 'images'} tidak ditemukan.")
    nama = ", ".join(f"'{k}'" for k in NAMA_KELAS)
    isi = (
        f"path: {folder}\n"
        "train: train/images\n"
        "val: valid/images\n"
        "test: test/images\n"
        f"nc: {len(NAMA_KELAS)}\n"
        f"names: [{nama}]\n"
    )
    tujuan = folder / "data.yaml"
    tujuan.write_text(isi, encoding="utf-8")
    return tujuan


def unduh_dari_roboflow(workspace: str, proyek: str, versi: int, folder: Path) -> Path:  # pragma: no cover
    """Mengunduh dataset format YOLOv8. API key dibaca dari environment ROBOFLOW_API_KEY, tidak ditulis di kode."""
    from roboflow import Roboflow

    api_key = os.environ.get("ROBOFLOW_API_KEY")
    if not api_key:
        raise RuntimeError("Isi ROBOFLOW_API_KEY lewat Colab Secrets sebelum mengunduh dataset.")
    dataset = Roboflow(api_key=api_key).workspace(workspace).project(proyek).version(versi)
    hasil = Path(dataset.download("yolov8", location=str(folder)).location)
    import yaml

    nama = yaml.safe_load((hasil / "data.yaml").read_text())["names"]
    if isinstance(nama, dict):
        nama = [nama[i] for i in sorted(nama)]
    if list(nama) != NAMA_KELAS:
        # Dataset dari Roboflow Universe sering memakai nama lain ("seven", "digit_7") atau punya kelas tambahan.
        print(f"{tulis_ulang_label(hasil, peta_kelas_digit(list(nama)))} kotak digit dipakai.")
    return tulis_data_yaml(hasil)
