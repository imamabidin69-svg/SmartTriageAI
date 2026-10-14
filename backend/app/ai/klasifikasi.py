"""Klasifikasi risk level dengan pola Strategy (Desain Gambar 2.14 dan baris 466).

FallbackClassifier membungkus RandomForestClassifier sebagai klasifikator utama dan RuleBasedClassifier
sebagai cadangan. Pemanggilnya (TriaseService) tidak perlu tahu hasilnya berasal dari model atau aturan;
asalnya dicatat di kolom sumber_rekomendasi.
"""

import logging
import math
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from app.ai.penjelasan import Faktor, LabelFitur, PenyusunPenjelasan, format_angka
from app.ai.registry import FITUR_MODEL, URUTAN_LEVEL, ModelTriase
from app.models.enums import JenisKelamin, KategoriKeluhan, RiskLevel, SumberRekomendasi, TingkatKesadaran

logger = logging.getLogger(__name__)

# Kode yang dipakai saat model dilatih (ml-service/app.py dan data KTAS).
KODE_JENIS_KELAMIN = {JenisKelamin.PEREMPUAN: 1, JenisKelamin.LAKI_LAKI: 2}
KODE_AVPU = {
    TingkatKesadaran.SADAR_PENUH: 1,
    TingkatKesadaran.RESPONS_SUARA: 2,
    TingkatKesadaran.RESPONS_NYERI: 3,
    TingkatKesadaran.TIDAK_RESPONS: 4,
}


@dataclass(frozen=True)
class FiturTriase:
    """Data satu triase yang dibutuhkan klasifikator, sudah tervalidasi oleh TriaseInput."""

    usia: int | None
    jenis_kelamin: JenisKelamin
    kategori_keluhan: KategoriKeluhan
    tingkat_kesadaran: TingkatKesadaran
    skala_nyeri: int
    td_sistolik: int
    td_diastolik: int
    nadi: int
    laju_napas: int
    suhu: Decimal
    saturasi: Decimal
    gejala: str

    def _map(self) -> float:
        return (self.td_sistolik + 2 * self.td_diastolik) / 3

    def _shock_index(self) -> float | None:
        return self.nadi / self.td_sistolik if self.td_sistolik else None

    def nilai_model(self) -> dict[str, Any]:
        """Nilai per kolom model dalam bentuk yang dibaca manusia, untuk label dan nilai faktor.

        map dan shock_index dibulatkan di sini hanya untuk tampilan; input model memakai baris_model().
        """
        shock_index = self._shock_index()
        return {
            "Sex": self.jenis_kelamin.value,
            "Age": self.usia,
            "kategori_keluhan": self.kategori_keluhan.value,
            "Mental": self.tingkat_kesadaran.value,
            "NRS_pain": self.skala_nyeri,
            "SBP": self.td_sistolik,
            "DBP": self.td_diastolik,
            "HR": self.nadi,
            "RR": self.laju_napas,
            "BT": float(self.suhu),
            "Saturation": float(self.saturasi),
            "map": round(self._map(), 2),
            "shock_index": None if shock_index is None else round(shock_index, 2),
        }

    def baris_model(self) -> dict[str, Any]:
        """Satu baris input pipeline dengan kode dan rumus yang sama persis seperti saat pelatihan.

        Fitur turunan tidak dibulatkan, sama dengan triase_data.tambah_fitur_turunan dan ml-service/app.py.
        Nilai kosong menjadi NaN lalu diisi median oleh imputer di dalam pipeline.
        """
        baris = {
            "Sex": KODE_JENIS_KELAMIN[self.jenis_kelamin],
            "Age": self.usia,
            "kategori_keluhan": self.kategori_keluhan.value,
            "Mental": KODE_AVPU[self.tingkat_kesadaran],
            "NRS_pain": self.skala_nyeri,
            "SBP": self.td_sistolik,
            "DBP": self.td_diastolik,
            "HR": self.nadi,
            "RR": self.laju_napas,
            "BT": float(self.suhu),
            "Saturation": float(self.saturasi),
            "map": self._map(),
            "shock_index": self._shock_index(),
        }
        return {kolom: (math.nan if isi is None else isi) for kolom, isi in baris.items()}


@dataclass(frozen=True)
class HasilKlasifikasi:
    risk_level: RiskLevel
    sumber: SumberRekomendasi
    penjelasan: list[Faktor]
    versi_model: str | None = None
    probabilitas: dict[str, float] | None = field(default=None)

    def penjelasan_json(self) -> dict[str, Any]:
        """Isi kolom penjelasan_ai (JSONB), dengan struktur yang sama untuk model dan aturan."""
        return {
            "versi_model": self.versi_model,
            "faktor": [faktor.ke_json() for faktor in self.penjelasan],
            "probabilitas": self.probabilitas,
        }


@dataclass(frozen=True)
class AmbangAturan:
    kritis: int
    tinggi: int
    sedang: int


class Classifier(ABC):
    @abstractmethod
    def klasifikasi(self, fitur: FiturTriase) -> HasilKlasifikasi:
        """Menghasilkan risk level beserta penjelasannya."""


class RandomForestClassifier(Classifier):
    """Random Forest 4 level dan explainer SHAP dari ModelRegistry.

    Bukan kelas scikit-learn dengan nama yang sama; namanya mengikuti class diagram Desain Gambar 2.14.
    """

    def __init__(self, model: ModelTriase) -> None:
        self.model = model

    def klasifikasi(self, fitur: FiturTriase) -> HasilKlasifikasi:
        import numpy as np
        import pandas as pd

        nilai = fitur.nilai_model()
        x_trans = self.model.prep.transform(pd.DataFrame([fitur.baris_model()], columns=list(FITUR_MODEL)))
        if hasattr(x_trans, "toarray"):
            x_trans = x_trans.toarray()

        proba = self.model.rf.predict_proba(x_trans)[0]
        indeks = int(np.argmax(proba))
        # SHAP 0.53 (versi yang dikunci) mengembalikan array berbentuk (baris, fitur, kelas).
        kontribusi = np.asarray(self.model.explainer.shap_values(x_trans))[0, :, indeks]

        faktor = PenyusunPenjelasan.dari_shap(kontribusi, self.model.nama_fitur_transformasi, x_trans[0], nilai)
        return HasilKlasifikasi(
            risk_level=URUTAN_LEVEL[indeks],
            sumber=SumberRekomendasi.MODEL,
            penjelasan=faktor,
            versi_model=self.model.versi,
            probabilitas={level.value: round(float(p), 4) for level, p in zip(URUTAN_LEVEL, proba, strict=True)},
        )


# Kata kunci gejala berisiko tinggi, sama persis dengan prototipe (lib/classify.ts).
KATA_KUNCI_GEJALA = re.compile(r"nyeri dada|sesak|tidak sadar|kejang|pendarahan hebat", re.IGNORECASE)
# Poin tingkat kesadaran ditambahkan atas persetujuan pengguna (K5); prototipe belum memakai AVPU.
POIN_AVPU = {
    TingkatKesadaran.RESPONS_SUARA: 1,
    TingkatKesadaran.RESPONS_NYERI: 3,
    TingkatKesadaran.TIDAK_RESPONS: 3,
}
# Saturasi 3 + sistolik 3 + nadi 2 + suhu 2 + napas 2 + kata kunci 3 + kesadaran 3.
SKOR_MAKSIMUM_ATURAN = 18


class RuleBasedClassifier(Classifier):
    """Aturan cadangan: poin tanda vital, kata kunci gejala, dan tingkat kesadaran (port lib/classify.ts)."""

    def __init__(self, ambang: AmbangAturan) -> None:
        self.ambang = ambang

    @staticmethod
    def aturan_terpicu(fitur: FiturTriase) -> list[Faktor]:
        terpicu: list[Faktor] = []

        def picu(nama: str | None, label: str, nilai: Any, poin: int) -> None:
            terpicu.append(Faktor(fitur=nama, label=label, nilai=nilai, kontribusi=poin, arah="naik"))

        saturasi = float(fitur.saturasi)
        if saturasi < 92:
            picu("Saturation", f"Saturasi oksigen rendah ({format_angka(saturasi)}%)", saturasi, 3)
        elif saturasi < 95:
            picu("Saturation", f"Saturasi oksigen agak rendah ({format_angka(saturasi)}%)", saturasi, 1)

        sistolik = fitur.td_sistolik
        if sistolik >= 180 or sistolik < 90:
            picu("SBP", f"Tekanan darah sistolik ekstrem ({sistolik} mmHg)", sistolik, 3)
        elif sistolik >= 150:
            picu("SBP", f"Tekanan darah sistolik tinggi ({sistolik} mmHg)", sistolik, 1)

        if fitur.nadi >= 120 or fitur.nadi < 50:
            picu("HR", f"Nadi tidak normal ({fitur.nadi} x/menit)", fitur.nadi, 2)

        suhu = float(fitur.suhu)
        if suhu >= 39:
            picu("BT", f"Demam tinggi ({format_angka(suhu)} °C)", suhu, 2)
        elif suhu >= 37.8:
            picu("BT", f"Demam ringan ({format_angka(suhu)} °C)", suhu, 1)

        if fitur.laju_napas >= 28 or fitur.laju_napas < 10:
            picu("RR", f"Laju napas tidak normal ({fitur.laju_napas} x/menit)", fitur.laju_napas, 2)

        cocok = KATA_KUNCI_GEJALA.search(fitur.gejala)
        if cocok:
            picu("gejala", "Kata kunci gejala berisiko tinggi pada uraian keluhan", cocok.group(0).lower(), 3)

        poin_avpu = POIN_AVPU.get(fitur.tingkat_kesadaran)
        if poin_avpu:
            label = LabelFitur.label("Mental", fitur.tingkat_kesadaran.value)
            picu("Mental", label, fitur.tingkat_kesadaran.value, poin_avpu)
        return terpicu

    def level_dari_skor(self, skor: int) -> RiskLevel:
        if skor >= self.ambang.kritis:
            return RiskLevel.KRITIS
        if skor >= self.ambang.tinggi:
            return RiskLevel.TINGGI
        if skor >= self.ambang.sedang:
            return RiskLevel.SEDANG
        return RiskLevel.RENDAH

    def klasifikasi(self, fitur: FiturTriase) -> HasilKlasifikasi:
        terpicu = self.aturan_terpicu(fitur)
        skor = int(sum(faktor.kontribusi for faktor in terpicu))
        return HasilKlasifikasi(
            risk_level=self.level_dari_skor(skor),
            sumber=SumberRekomendasi.ATURAN,
            penjelasan=PenyusunPenjelasan.dari_aturan(terpicu),
        )


class FallbackClassifier(Classifier):
    """Memakai klasifikator utama, lalu aturan cadangan bila model tidak ada atau error (NFR-03)."""

    def __init__(self, utama: Classifier | None, cadangan: Classifier) -> None:
        self.utama = utama
        self.cadangan = cadangan

    def klasifikasi(self, fitur: FiturTriase) -> HasilKlasifikasi:
        if self.utama is not None:
            try:
                return self.utama.klasifikasi(fitur)
            except Exception:
                # Sengaja menangkap semua error: rekomendasi tetap harus keluar lewat jalur cadangan.
                logger.warning("Klasifikasi model gagal, memakai aturan cadangan.", exc_info=True)
        return self.cadangan.klasifikasi(fitur)


def buat_klasifikator(model: ModelTriase | None, ambang: AmbangAturan) -> Classifier:
    utama = RandomForestClassifier(model) if model is not None else None
    return FallbackClassifier(utama=utama, cadangan=RuleBasedClassifier(ambang))
