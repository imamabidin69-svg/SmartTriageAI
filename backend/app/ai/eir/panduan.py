"""Panduan anamnesis dan GuidelineRetriever (FR-08, Desain 2.8, 7.2, dan baris 482).

Panduan disimpan sebagai enam berkas Markdown di app/ai/artefak/panduan, satu per topik riwayat yang digali
dari keluarga pasien ICU, lalu diindeks TF-IDF sekali saat aplikasi dinyalakan. Panduan tidak disimpan di
basis data.
"""

import re
from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from app.models.enums import TopikAnamnesis

JUMLAH_PANDUAN = len(TopikAnamnesis)
# Kata kunci diulang supaya istilah sehari-hari ("darah tinggi", "obat jantung") lebih berbobot dari isi panjang.
BOBOT_KATA_KUNCI = 3


class PanduanTidakSesuaiError(ValueError):
    """Isi folder panduan tidak lengkap atau formatnya tidak dikenali."""


@dataclass(frozen=True)
class Panduan:
    nama_berkas: str
    topik: TopikAnamnesis
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
    nama_topik = _baris_awalan(teks, "Topik", path.name)
    try:
        topik = TopikAnamnesis(nama_topik)
    except ValueError as galat:
        raise PanduanTidakSesuaiError(f"Topik '{nama_topik}' di {path.name} tidak dikenal.") from galat
    kata_kunci = tuple(k.strip() for k in _baris_awalan(teks, "Kata kunci", path.name).split(",") if k.strip())
    bagian = re.search(r"^## Pertanyaan inti\s*$(.*?)(?=^## |\Z)", teks, re.MULTILINE | re.DOTALL)
    pertanyaan = tuple(re.findall(r"^- (.+)$", bagian.group(1), re.MULTILINE)) if bagian else ()
    if not pertanyaan:
        raise PanduanTidakSesuaiError(f"Panduan {path.name} tidak punya daftar pertanyaan inti.")
    return Panduan(path.name, topik, kata_kunci, pertanyaan, teks.strip())


def muat_panduan(folder: Path) -> list[Panduan]:
    """Membaca semua panduan. Satu topik tepat satu berkas, supaya tidak ada topik tanpa panduan."""
    daftar = [baca_panduan(path) for path in sorted(folder.glob("*.md"))]
    topik = [p.topik for p in daftar]
    if len(daftar) != JUMLAH_PANDUAN or set(topik) != set(TopikAnamnesis):
        kurang = sorted(k.value for k in set(TopikAnamnesis) - set(topik))
        raise PanduanTidakSesuaiError(
            f"Folder panduan harus berisi {JUMLAH_PANDUAN} berkas, satu per topik. "
            f"Ditemukan {len(daftar)} berkas; topik tanpa panduan: {kurang or '-'}."
        )
    return daftar


class GuidelineRetriever:
    """Mencari panduan paling relevan dengan TF-IDF n-gram karakter.

    N-gram karakter dipilih karena bahasa chat penuh imbuhan dan ejaan bebas ("diopname", "kencing manis"),
    yang tetap berbagi potongan huruf dengan kata dasarnya di panduan.
    """

    def __init__(self, panduan: list[Panduan]) -> None:
        self.panduan = panduan
        self.tfidf = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True, lowercase=True)
        dokumen = [" ".join([p.topik.value, *(p.kata_kunci * BOBOT_KATA_KUNCI), p.isi]) for p in panduan]
        self.matriks = self.tfidf.fit_transform(dokumen)

    def cari(self, teks: str, k: int = 3) -> list[Panduan]:
        skor = linear_kernel(self.tfidf.transform([teks]), self.matriks).ravel()
        # Urutan stabil: skor sama (misalnya teks tanpa huruf) tetap mengikuti urutan berkas.
        urutan = sorted(range(len(self.panduan)), key=lambda i: -skor[i])
        return [self.panduan[i] for i in urutan[:k]]
