"""Panduan anamnesis dan GuidelineRetriever (FR-08, Desain 2.8, 7.2, dan baris 482).

Panduan disimpan sebagai 18 berkas Markdown di app/ai/artefak/panduan, satu per kategori keluhan, lalu
diindeks TF-IDF sekali saat aplikasi dinyalakan. Panduan tidak disimpan di basis data.
"""

import re
from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from app.models.enums import KategoriKeluhan

JUMLAH_PANDUAN = len(KategoriKeluhan)
# Kata kunci diulang supaya istilah sehari-hari ("mencret", "deg-degan") lebih berbobot dari isi panjang.
BOBOT_KATA_KUNCI = 3


class PanduanTidakSesuaiError(ValueError):
    """Isi folder panduan tidak lengkap atau formatnya tidak dikenali."""


@dataclass(frozen=True)
class Panduan:
    nama_berkas: str
    kategori: KategoriKeluhan
    kata_kunci: tuple[str, ...]
    pertanyaan: tuple[str, ...]
    isi: str


def _baris_awalan(teks: str, awalan: str, berkas: str) -> str:
    cocok = re.search(rf"^{awalan}:\s*(.+)$", teks, re.MULTILINE)
    if not cocok:
        raise PanduanTidakSesuaiError(f"Panduan {berkas} tidak punya baris '{awalan}:'.")
    return cocok.group(1).strip()


def baca_panduan(path: Path) -> Panduan:
    teks = path.read_text(encoding="utf-8")
    nama_kategori = _baris_awalan(teks, "Kategori", path.name)
    try:
        kategori = KategoriKeluhan(nama_kategori)
    except ValueError as galat:
        raise PanduanTidakSesuaiError(f"Kategori '{nama_kategori}' di {path.name} tidak dikenal.") from galat
    kata_kunci = tuple(k.strip() for k in _baris_awalan(teks, "Kata kunci", path.name).split(",") if k.strip())
    bagian = re.search(r"^## Pertanyaan inti\s*$(.*?)(?=^## |\Z)", teks, re.MULTILINE | re.DOTALL)
    pertanyaan = tuple(re.findall(r"^- (.+)$", bagian.group(1), re.MULTILINE)) if bagian else ()
    if not pertanyaan:
        raise PanduanTidakSesuaiError(f"Panduan {path.name} tidak punya daftar pertanyaan inti.")
    return Panduan(path.name, kategori, kata_kunci, pertanyaan, teks.strip())


def muat_panduan(folder: Path) -> list[Panduan]:
    """Membaca semua panduan. Satu kategori tepat satu berkas, supaya tidak ada keluhan tanpa panduan."""
    daftar = [baca_panduan(path) for path in sorted(folder.glob("*.md"))]
    kategori = [p.kategori for p in daftar]
    if len(daftar) != JUMLAH_PANDUAN or set(kategori) != set(KategoriKeluhan):
        kurang = sorted(k.value for k in set(KategoriKeluhan) - set(kategori))
        raise PanduanTidakSesuaiError(
            f"Folder panduan harus berisi {JUMLAH_PANDUAN} berkas, satu per kategori keluhan. "
            f"Ditemukan {len(daftar)} berkas; kategori tanpa panduan: {kurang or '-'}."
        )
    return daftar


class GuidelineRetriever:
    """Mencari panduan paling relevan dengan TF-IDF n-gram karakter.

    N-gram karakter dipilih karena bahasa chat penuh imbuhan dan ejaan bebas ("kesakitan", "bernafas"),
    yang tetap berbagi potongan huruf dengan kata dasarnya di panduan.
    """

    def __init__(self, panduan: list[Panduan]) -> None:
        self.panduan = panduan
        self.tfidf = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True, lowercase=True)
        dokumen = [" ".join([p.kategori.value, *(p.kata_kunci * BOBOT_KATA_KUNCI), p.isi]) for p in panduan]
        self.matriks = self.tfidf.fit_transform(dokumen)

    def cari(self, teks: str, k: int = 3) -> list[Panduan]:
        skor = linear_kernel(self.tfidf.transform([teks]), self.matriks).ravel()
        # Urutan stabil: skor sama (misalnya teks tanpa huruf) tetap mengikuti urutan berkas.
        urutan = sorted(range(len(self.panduan)), key=lambda i: -skor[i])
        return [self.panduan[i] for i in urutan[:k]]
