"""Menyiapkan dataset digit dari Roboflow untuk pelatihan YOLO.

Setiap digit 0 sampai 9 pada foto layar alat dianotasi sebagai kelas tersendiri (Desain 7.3). Urutan
kelas di model harus 0-9, karena backend membaca indeks kelas langsung sebagai nilai digit.
"""

import os
from pathlib import Path

NAMA_KELAS = [str(i) for i in range(10)]


class DatasetTidakSesuaiError(ValueError):
    """Kelas atau struktur dataset tidak sesuai detektor digit 0-9."""


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

    periksa_kelas(yaml.safe_load((hasil / "data.yaml").read_text())["names"])
    return tulis_data_yaml(hasil)
