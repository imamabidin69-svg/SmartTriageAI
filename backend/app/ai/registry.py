"""ModelRegistry: memuat bundle Random Forest, explainer SHAP, dan model YOLO saat aplikasi start.

Bundle berasal dari prototipe (ml-service/latih_model.py) dan berupa dict berisi Pipeline
(ColumnTransformer + RandomForestClassifier), daftar fitur, urutan level, dan versi model.
Explainer tidak ikut tersimpan, jadi dibuat ulang dengan shap.TreeExplainer seperti di prototipe.

Bila berkas tidak ada atau isinya tidak sesuai, aplikasi tetap berjalan dengan aturan cadangan
dan health check menjadi degraded (NFR-03).
"""

import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from flask import current_app

from app.ai.pembaca_layar import PembacaLayar, PembacaLayarOnnx, PembacaLayarTiruan
from app.models.enums import KategoriKeluhan, RiskLevel

logger = logging.getLogger(__name__)

# Urutan kolom yang dipakai saat model dilatih (ml-service/triase_data.py, FITUR_LENGKAP).
FITUR_MODEL = (
    "Sex",
    "Age",
    "kategori_keluhan",
    "Mental",
    "NRS_pain",
    "SBP",
    "DBP",
    "HR",
    "RR",
    "BT",
    "Saturation",
    "map",
    "shock_index",
)
URUTAN_LEVEL = (RiskLevel.RENDAH, RiskLevel.SEDANG, RiskLevel.TINGGI, RiskLevel.KRITIS)


class BundleTidakSesuaiError(ValueError):
    """Isi bundle tidak cocok dengan fitur dan level yang dipakai backend."""


@dataclass(frozen=True)
class ModelTriase:
    prep: Any
    rf: Any
    explainer: Any
    nama_fitur_transformasi: tuple[str, ...]
    versi: str


def _periksa_bundle(bundle: Any) -> None:
    if not isinstance(bundle, dict):
        raise BundleTidakSesuaiError("Bundle model harus berupa dict.")
    for kunci in ("model", "fitur", "urutan_level", "kategori_keluhan_dikenal", "versi"):
        if kunci not in bundle:
            raise BundleTidakSesuaiError(f"Bundle model tidak punya kunci '{kunci}'.")
    if tuple(bundle["fitur"]) != FITUR_MODEL:
        raise BundleTidakSesuaiError(f"Fitur bundle {bundle['fitur']} tidak sama dengan {list(FITUR_MODEL)}.")
    if tuple(bundle["urutan_level"]) != tuple(level.value for level in URUTAN_LEVEL):
        raise BundleTidakSesuaiError(f"Urutan level bundle {bundle['urutan_level']} tidak dikenal.")
    if set(bundle["kategori_keluhan_dikenal"]) != {kategori.value for kategori in KategoriKeluhan}:
        raise BundleTidakSesuaiError("Kategori keluhan bundle tidak sama dengan 18 kategori di basis data.")
    rf = bundle["model"].named_steps["model"]
    if list(rf.classes_) != list(range(len(URUTAN_LEVEL))):
        raise BundleTidakSesuaiError(f"Kelas model {list(rf.classes_)} tidak sama dengan kode level 0-3.")


@lru_cache(maxsize=4)
def _muat_dari_berkas(path: str, waktu_ubah: float) -> ModelTriase:
    """Disimpan per path dan waktu ubah berkas, supaya instance aplikasi kedua (misalnya di tes) tidak memuat ulang."""
    # Impor di sini supaya scikit-learn dan SHAP hanya dimuat bila memang ada model.
    import joblib
    import shap

    del waktu_ubah  # hanya dipakai sebagai bagian kunci cache
    bundle = joblib.load(path)
    _periksa_bundle(bundle)
    pipeline = bundle["model"]
    prep = pipeline.named_steps["prep"]
    rf = pipeline.named_steps["model"]
    # Model dilatih dengan n_jobs=-1. Untuk satu baris per request, satu thread justru lebih cepat
    # dan tidak berebut CPU dengan worker Gunicorn lain.
    rf.set_params(n_jobs=1)
    return ModelTriase(
        prep=prep,
        rf=rf,
        explainer=shap.TreeExplainer(rf),
        nama_fitur_transformasi=tuple(prep.get_feature_names_out()),
        versi=str(bundle["versi"]),
    )


class ModelRegistry:
    def __init__(self) -> None:
        self.model_triase: ModelTriase | None = None
        self.pembaca_layar: PembacaLayar | None = None

    @property
    def termuat(self) -> bool:
        return self.model_triase is not None

    @property
    def versi_model(self) -> str | None:
        return self.model_triase.versi if self.model_triase else None

    def muat(self, path_model_rf: str | None) -> None:
        self.model_triase = None
        if not path_model_rf:
            logger.warning("MODEL_RF_PATH kosong. Rekomendasi triase memakai aturan cadangan.")
            return
        berkas = Path(path_model_rf)
        try:
            self.model_triase = _muat_dari_berkas(str(berkas.resolve()), berkas.stat().st_mtime)
        except FileNotFoundError:
            logger.error("Model triase tidak ditemukan di %s. Rekomendasi memakai aturan cadangan.", berkas)
        except Exception:
            logger.exception("Model triase gagal dimuat dari %s. Rekomendasi memakai aturan cadangan.", berkas)
        else:
            logger.info("Model triase %s dimuat dari %s.", self.model_triase.versi, berkas)

    def muat_pembaca_layar(self, path_model_yolo: str | None, mode: str = "onnx") -> None:
        """Tanpa pembaca layar, pemindaian tetap tersimpan tetapi kolomnya dibiarkan kosong (Desain baris 396)."""
        self.pembaca_layar = None
        if mode == "tiruan":
            self.pembaca_layar = PembacaLayarTiruan()
            logger.warning("Pembaca layar memakai mode tiruan. Angka hasil pemindaian hanya contoh.")
            return
        if not path_model_yolo:
            logger.warning("MODEL_YOLO_PATH kosong. Kolom hasil pemindaian akan diisi manual.")
            return
        try:
            self.pembaca_layar = PembacaLayarOnnx(path_model_yolo)
        except FileNotFoundError:
            logger.warning("Model YOLO belum ada di %s. Kolom hasil pemindaian akan diisi manual.", path_model_yolo)
        except Exception:
            logger.exception("Model YOLO gagal dimuat dari %s. Kolom pemindaian akan diisi manual.", path_model_yolo)
        else:
            logger.info("Model YOLO pembaca layar dimuat dari %s.", path_model_yolo)


def model_registry() -> ModelRegistry:
    return current_app.extensions["model_registry"]
