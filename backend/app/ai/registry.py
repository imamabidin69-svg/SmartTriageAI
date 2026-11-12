"""ModelRegistry: memuat bundle Random Forest, explainer SHAP, model YOLO, dan indeks panduan Eir saat aplikasi start.

Bundle dibuat oleh ai_training/perburukan.py dan berupa dict berisi Pipeline (ColumnTransformer +
RandomForestClassifier dua kelas), daftar fitur, ambang peluang tiap level, dan versi model.
Explainer tidak ikut tersimpan, jadi dibuat ulang dengan shap.TreeExplainer saat dimuat.

Bila berkas tidak ada atau isinya tidak sesuai, aplikasi tetap berjalan dengan aturan cadangan
dan health check menjadi degraded (NFR-03).
"""

import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from flask import current_app

from app.ai.eir.llm import GroqClient, LlmClient, LlmTiruan
from app.ai.eir.panduan import GuidelineRetriever, muat_panduan
from app.ai.pembaca_layar import PembacaLayar, PembacaLayarOnnx, PembacaLayarTiruan
from app.models.enums import RiskLevel

logger = logging.getLogger(__name__)

# Urutan kolom saat model perburukan ICU dilatih (ai_training/perburukan.py, data PhysioNet 2019).
FITUR_MODEL = (
    "nadi",
    "saturasi",
    "suhu",
    "td_sistolik",
    "td_diastolik",
    "map",
    "laju_napas",
    "laktat",
    "kreatinin",
    "trombosit",
    "leukosit",
    "bilirubin",
    "usia",
    "jenis_kelamin",
    "shock_index",
)
# Level yang punya ambang peluang, dari yang terendah. Di bawah ambang sedang berarti Rendah.
LEVEL_AMBANG = ("sedang", "tinggi", "kritis")


class BundleTidakSesuaiError(ValueError):
    """Isi bundle tidak cocok dengan fitur dan level yang dipakai backend."""


@dataclass(frozen=True)
class ModelPerburukan:
    prep: Any
    rf: Any
    explainer: Any
    nama_fitur_transformasi: tuple[str, ...]
    ambang: dict[str, float]
    versi: str

    def level(self, peluang: float) -> RiskLevel:
        hasil = RiskLevel.RENDAH
        for nama in LEVEL_AMBANG:
            if peluang >= self.ambang[nama]:
                hasil = RiskLevel(nama)
        return hasil


def _periksa_bundle(bundle: Any) -> None:
    if not isinstance(bundle, dict):
        raise BundleTidakSesuaiError("Bundle model harus berupa dict.")
    for kunci in ("model", "fitur", "ambang", "versi"):
        if kunci not in bundle:
            raise BundleTidakSesuaiError(f"Bundle model tidak punya kunci '{kunci}'.")
    if tuple(bundle["fitur"]) != FITUR_MODEL:
        raise BundleTidakSesuaiError(f"Fitur bundle {bundle['fitur']} tidak sama dengan {list(FITUR_MODEL)}.")
    ambang = bundle["ambang"]
    if not isinstance(ambang, dict) or set(ambang) != set(LEVEL_AMBANG):
        raise BundleTidakSesuaiError(f"Ambang bundle harus berisi {list(LEVEL_AMBANG)}.")
    nilai = [float(ambang[nama]) for nama in LEVEL_AMBANG]
    if nilai != sorted(nilai) or not all(0 <= n <= 1 for n in nilai):
        raise BundleTidakSesuaiError(f"Ambang bundle {ambang} harus urut naik di antara 0 dan 1.")
    rf = bundle["model"].named_steps["model"]
    if list(rf.classes_) != [0, 1]:
        raise BundleTidakSesuaiError(f"Kelas model {list(rf.classes_)} bukan 0 (stabil) dan 1 (memburuk).")


@lru_cache(maxsize=4)
def _muat_dari_berkas(path: str, waktu_ubah: float) -> ModelPerburukan:
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
    # Untuk satu baris per request, satu thread lebih cepat dan tidak berebut CPU dengan worker Gunicorn lain.
    rf.set_params(n_jobs=1)
    return ModelPerburukan(
        prep=prep,
        rf=rf,
        explainer=shap.TreeExplainer(rf),
        nama_fitur_transformasi=tuple(prep.get_feature_names_out()),
        ambang={nama: float(bundle["ambang"][nama]) for nama in LEVEL_AMBANG},
        versi=str(bundle["versi"]),
    )


class ModelRegistry:
    def __init__(self) -> None:
        self.model_perburukan: ModelPerburukan | None = None
        self.pembaca_layar: PembacaLayar | None = None
        self.retriever: GuidelineRetriever | None = None
        self.llm: LlmClient | None = None

    @property
    def termuat(self) -> bool:
        return self.model_perburukan is not None

    @property
    def versi_model(self) -> str | None:
        return self.model_perburukan.versi if self.model_perburukan else None

    def muat(self, path_model_rf: str | None) -> None:
        self.model_perburukan = None
        if not path_model_rf:
            logger.warning("MODEL_RF_PATH kosong. Penilaian prioritas memakai NEWS2 saja.")
            return
        berkas = Path(path_model_rf)
        try:
            self.model_perburukan = _muat_dari_berkas(str(berkas.resolve()), berkas.stat().st_mtime)
        except FileNotFoundError:
            logger.error("Model perburukan tidak ditemukan di %s. Penilaian memakai NEWS2 saja.", berkas)
        except Exception:
            logger.exception("Model perburukan gagal dimuat dari %s. Penilaian memakai NEWS2 saja.", berkas)
        else:
            logger.info("Model perburukan %s dimuat dari %s.", self.model_perburukan.versi, berkas)

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

    def muat_eir(self, folder_panduan: str | None, mode_llm: str = "groq", **groq: Any) -> None:
        """Tanpa panduan atau LLM, Eir membalas 503 tetapi deteksi tanda bahaya tetap berjalan (Desain baris 396)."""
        self.retriever = None
        try:
            self.retriever = GuidelineRetriever(muat_panduan(Path(folder_panduan or "")))
        except Exception:
            logger.exception("Panduan Eir gagal dimuat dari %s. Eir tidak dapat menyusun pertanyaan.", folder_panduan)
        else:
            logger.info("%d panduan anamnesis Eir dimuat dari %s.", len(self.retriever.panduan), folder_panduan)

        self.llm = None
        if mode_llm == "tiruan":
            self.llm = LlmTiruan()
            logger.warning("Eir memakai LLM tiruan. Pertanyaan dan ringkasan hanya contoh.")
        elif not groq.get("api_key"):
            logger.warning("GROQ_API_KEY kosong. Eir tidak dapat menyusun pertanyaan.")
        else:
            self.llm = GroqClient(**groq)


def model_registry() -> ModelRegistry:
    return current_app.extensions["model_registry"]
