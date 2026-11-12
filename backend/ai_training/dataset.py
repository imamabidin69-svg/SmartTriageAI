"""Menyiapkan dataset digit dari Roboflow untuk pelatihan YOLO.

Setiap digit 0 sampai 9 pada foto layar alat dianotasi sebagai kelas tersendiri (Desain 7.3). Urutan
kelas di model harus 0-9, karena backend membaca indeks kelas langsung sebagai nilai digit.
"""

import argparse
import ast
import os
import shutil
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


def baca_nama_kelas(data_yaml: Path) -> list[str]:
    """Membaca daftar kelas dari data.yaml ekspor Roboflow tanpa PyYAML.

    Roboflow menulis kelas sebagai list satu baris (names: ['0', '1']) atau sebagai blok per baris
    ("- 0" atau "0: digit"). Keduanya didukung.
    """
    baris = Path(data_yaml).read_text(encoding="utf-8").splitlines()
    for i, isi in enumerate(baris):
        if not isi.startswith("names:"):
            continue
        sisa = isi.removeprefix("names:").strip()
        if sisa:
            return [str(n) for n in ast.literal_eval(sisa)]
        nama = []
        for lanjut in baris[i + 1 :]:
            if not lanjut.startswith((" ", "\t", "-")) or not lanjut.strip():
                break
            item = lanjut.strip().removeprefix("-").strip()
            if ":" in item and not item.startswith(("'", '"')):
                item = item.split(":", 1)[1].strip()
            nama.append(item.strip("'\""))
        return nama
    raise DatasetTidakSesuaiError(f"Daftar kelas (names) tidak ditemukan di {data_yaml}.")


def _baris_kotak(baris: str, peta: dict[int, int]) -> str | None:
    """Satu baris label YOLO menjadi kotak digit. Label poligon (segmentasi atau OBB) diubah ke kotak pembatasnya."""
    bagian = baris.split()
    if not bagian or int(bagian[0]) not in peta:
        return None
    angka = [float(x) for x in bagian[1:]]
    if len(angka) == 4:
        xc, yc, w, h = angka
    else:
        xs, ys = angka[0::2], angka[1::2]
        xc, yc, w, h = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, max(xs) - min(xs), max(ys) - min(ys)
    if w <= 0 or h <= 0:
        return None
    return f"{peta[int(bagian[0])]} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}"


def gabung_dataset(sumber: list[Path], tujuan: Path) -> dict[str, dict[str, int]]:
    """Menggabungkan beberapa ekspor YOLOv8 Roboflow menjadi satu dataset digit 0-9.

    Kelas setiap dataset dipetakan ke 0-9 dengan peta_kelas_digit, kelas lain (titik, minus, "bp-monitor")
    dibuang, dan nama berkas diberi awalan d0_, d1_, dan seterusnya supaya tidak bertabrakan. Bagian yang
    tidak ada (misalnya dataset tanpa test) dilewati. Mengembalikan jumlah foto dan kotak per dataset.
    """
    tujuan = Path(tujuan)
    if tujuan.exists():
        shutil.rmtree(tujuan)
    for bagian in ("train", "valid", "test"):
        (tujuan / bagian / "images").mkdir(parents=True)
        (tujuan / bagian / "labels").mkdir(parents=True)
    statistik: dict[str, dict[str, int]] = {}
    for i, folder in enumerate(Path(s) for s in sumber):
        peta = peta_kelas_digit(baca_nama_kelas(folder / "data.yaml"))
        hitung = statistik.setdefault(folder.name, {"foto": 0, "kotak": 0})
        for bagian in ("train", "valid", "test"):
            for gambar in sorted((folder / bagian / "images").glob("*")):
                label = folder / bagian / "labels" / f"{gambar.stem}.txt"
                isi = label.read_text(encoding="utf-8").splitlines() if label.exists() else []
                kotak = [k for k in (_baris_kotak(b, peta) for b in isi) if k]
                nama = f"d{i}_{gambar.stem}"
                shutil.copy2(gambar, tujuan / bagian / "images" / f"{nama}{gambar.suffix.lower()}")
                teks = "\n".join(kotak) + ("\n" if kotak else "")
                (tujuan / bagian / "labels" / f"{nama}.txt").write_text(teks, encoding="utf-8")
                hitung["foto"] += 1
                hitung["kotak"] += len(kotak)
    tulis_data_yaml(tujuan)
    return statistik


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


if __name__ == "__main__":  # pragma: no cover
    parser = argparse.ArgumentParser(description="Gabungkan ekspor YOLOv8 Roboflow menjadi dataset digit 0-9.")
    parser.add_argument("--sumber", type=Path, nargs="+", required=True, help="Folder hasil ekstrak zip Roboflow.")
    parser.add_argument("--tujuan", type=Path, required=True)
    a = parser.parse_args()
    for nama, jumlah in gabung_dataset(a.sumber, a.tujuan).items():
        print(f"{nama}: {jumlah['foto']} foto, {jumlah['kotak']} kotak digit")
    print(f"data.yaml: {a.tujuan / 'data.yaml'}")
