"""Penilaian prioritas pasien ICU: NEWS2 ditambah model peluang perburukan (pola Strategy, Desain Gambar 2.14).

NEWS2 selalu dihitung karena hanya butuh tanda vital, kesadaran, dan oksigen. Bila model Random Forest
tersedia, peluang perburukannya ikut menentukan level; level akhir adalah yang lebih tinggi dari keduanya,
supaya model tidak pernah menurunkan level yang sudah ditunjukkan NEWS2. Bila model tidak ada atau error,
penilaian tetap keluar dari NEWS2 saja dan sumber_rekomendasi dicatat "aturan" (NFR-03).
"""

import logging
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from app.ai.news2 import AmbangNews2, HasilNews2, hitung_news2
from app.ai.penjelasan import Faktor, PenyusunPenjelasan
from app.ai.registry import FITUR_MODEL, ModelPerburukan
from app.models.enums import JenisKelamin, RiskLevel, SumberRekomendasi, TingkatKesadaran

logger = logging.getLogger(__name__)

# Kode jenis kelamin saat model dilatih (PhysioNet 2019: 0 perempuan, 1 laki-laki).
KODE_JENIS_KELAMIN = {JenisKelamin.PEREMPUAN: 0, JenisKelamin.LAKI_LAKI: 1}
URUTAN_LEVEL = (RiskLevel.RENDAH, RiskLevel.SEDANG, RiskLevel.TINGGI, RiskLevel.KRITIS)


def level_tertinggi(*level: RiskLevel) -> RiskLevel:
    return max(level, key=URUTAN_LEVEL.index)


def _angka(nilai: Decimal | int | None) -> float | None:
    return None if nilai is None else float(nilai)


@dataclass(frozen=True)
class DataObservasi:
    """Data satu observasi yang dibutuhkan penilai, sudah tervalidasi oleh TriaseInput."""

    usia: int | None
    jenis_kelamin: JenisKelamin
    tingkat_kesadaran: TingkatKesadaran
    oksigen_tambahan: bool
    td_sistolik: int
    td_diastolik: int
    nadi: int
    laju_napas: int
    suhu: Decimal
    saturasi: Decimal
    laktat: Decimal | None = None
    kreatinin: Decimal | None = None
    trombosit: int | None = None
    leukosit: Decimal | None = None
    bilirubin: Decimal | None = None

    def _map(self) -> float:
        return (self.td_sistolik + 2 * self.td_diastolik) / 3

    def _shock_index(self) -> float | None:
        return self.nadi / self.td_sistolik if self.td_sistolik else None

    def nilai_model(self) -> dict[str, Any]:
        """Nilai per kolom model dalam bentuk yang dibaca manusia, untuk label faktor penjelas."""
        shock_index = self._shock_index()
        return {
            "nadi": self.nadi,
            "saturasi": float(self.saturasi),
            "suhu": float(self.suhu),
            "td_sistolik": self.td_sistolik,
            "td_diastolik": self.td_diastolik,
            "map": round(self._map(), 1),
            "laju_napas": self.laju_napas,
            "laktat": _angka(self.laktat),
            "kreatinin": _angka(self.kreatinin),
            "trombosit": self.trombosit,
            "leukosit": _angka(self.leukosit),
            "bilirubin": _angka(self.bilirubin),
            "usia": self.usia,
            "jenis_kelamin": self.jenis_kelamin.value,
            "shock_index": None if shock_index is None else round(shock_index, 2),
        }

    def baris_model(self) -> dict[str, Any]:
        """Satu baris input pipeline dengan kode dan rumus yang sama seperti ai_training/perburukan.py.

        Hasil lab yang kosong menjadi NaN lalu diisi median oleh imputer di dalam pipeline.
        """
        baris = {**self.nilai_model(), "jenis_kelamin": KODE_JENIS_KELAMIN[self.jenis_kelamin]}
        baris["map"] = self._map()
        baris["shock_index"] = self._shock_index()
        return {kolom: (math.nan if baris[kolom] is None else baris[kolom]) for kolom in FITUR_MODEL}


@dataclass(frozen=True)
class HasilModel:
    peluang: float
    level: RiskLevel
    faktor: list[Faktor]
    versi: str


@dataclass(frozen=True)
class HasilPenilaian:
    news2: HasilNews2
    model: HasilModel | None

    @property
    def risk_level(self) -> RiskLevel:
        if self.model is None:
            return self.news2.level
        return level_tertinggi(self.news2.level, self.model.level)

    @property
    def sumber(self) -> SumberRekomendasi:
        return SumberRekomendasi.ATURAN if self.model is None else SumberRekomendasi.MODEL

    @property
    def peluang(self) -> Decimal | None:
        return None if self.model is None else Decimal(str(round(self.model.peluang, 4)))

    def penjelasan_json(self) -> dict[str, Any]:
        """Isi kolom penjelasan_ai (JSONB)."""
        return {
            "versi_model": self.model.versi if self.model else None,
            "skor_news2": self.news2.skor,
            "level_news2": self.news2.level.value,
            "komponen_news2": [faktor.ke_json() for faktor in self.news2.komponen],
            "peluang_perburukan": float(self.peluang) if self.peluang is not None else None,
            "level_model": self.model.level.value if self.model else None,
            "faktor": [faktor.ke_json() for faktor in self.model.faktor] if self.model else [],
        }


class Classifier(ABC):
    @abstractmethod
    def klasifikasi(self, data: DataObservasi) -> Any:
        """Menilai satu observasi."""


class RuleBasedClassifier(Classifier):
    """NEWS2, dengan ambang level dari tabel konfigurasi."""

    def __init__(self, ambang: AmbangNews2) -> None:
        self.ambang = ambang

    def klasifikasi(self, data: DataObservasi) -> HasilNews2:
        return hitung_news2(
            laju_napas=data.laju_napas,
            saturasi=data.saturasi,
            oksigen_tambahan=data.oksigen_tambahan,
            td_sistolik=data.td_sistolik,
            nadi=data.nadi,
            tingkat_kesadaran=data.tingkat_kesadaran,
            suhu=data.suhu,
            ambang=self.ambang,
        )


class RandomForestClassifier(Classifier):
    """Random Forest peluang perburukan dan explainer SHAP dari ModelRegistry.

    Bukan kelas scikit-learn dengan nama yang sama; namanya mengikuti class diagram Desain Gambar 2.14.
    """

    def __init__(self, model: ModelPerburukan) -> None:
        self.model = model

    def klasifikasi(self, data: DataObservasi) -> HasilModel:
        import numpy as np
        import pandas as pd

        x_trans = self.model.prep.transform(pd.DataFrame([data.baris_model()], columns=list(FITUR_MODEL)))
        peluang = float(self.model.rf.predict_proba(x_trans)[0, 1])
        # SHAP 0.53 (versi yang dikunci) mengembalikan array berbentuk (baris, fitur, kelas); kelas 1 = memburuk.
        kontribusi = np.asarray(self.model.explainer.shap_values(x_trans))[0, :, 1]
        faktor = PenyusunPenjelasan.dari_shap(kontribusi, self.model.nama_fitur_transformasi, data.nilai_model())
        return HasilModel(peluang=peluang, level=self.model.level(peluang), faktor=faktor, versi=self.model.versi)


class FallbackClassifier(Classifier):
    """NEWS2 selalu dihitung; model ditambahkan bila ada dan tidak error (NFR-03)."""

    def __init__(self, utama: RandomForestClassifier | None, cadangan: RuleBasedClassifier) -> None:
        self.utama = utama
        self.cadangan = cadangan

    def klasifikasi(self, data: DataObservasi) -> HasilPenilaian:
        news2 = self.cadangan.klasifikasi(data)
        model = None
        if self.utama is not None:
            try:
                model = self.utama.klasifikasi(data)
            except Exception:
                # Sengaja menangkap semua error: penilaian tetap harus keluar lewat NEWS2.
                logger.warning("Model perburukan gagal, penilaian memakai NEWS2 saja.", exc_info=True)
        return HasilPenilaian(news2=news2, model=model)


def buat_klasifikator(model: ModelPerburukan | None, ambang: AmbangNews2) -> FallbackClassifier:
    utama = RandomForestClassifier(model) if model is not None else None
    return FallbackClassifier(utama=utama, cadangan=RuleBasedClassifier(ambang))
