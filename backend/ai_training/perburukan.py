"""Melatih model peluang perburukan pasien ICU dari data PhysioNet Computing in Cardiology Challenge 2019.

Data: 40.336 pasien ICU dari dua rumah sakit di Amerika Serikat, satu baris per jam (lisensi CC BY 4.0,
https://physionet.org/content/challenge-2019/1.0.0/). Kolom SepsisLabel bernilai 1 mulai 6 jam sebelum
sepsis terdiagnosis, jadi dipakai sebagai label "pasien akan memburuk dalam 6 jam ke depan".

Model hanya memakai data yang bisa dicatat perawat ICU di samping bed: tanda vital, lima hasil
laboratorium yang boleh kosong, usia, dan jenis kelamin. Nilai yang belum pernah diukur dibiarkan
kosong lalu diisi median oleh imputer, sama seperti saat backend menerima observasi tanpa hasil lab.

Contoh: python -m ai_training.perburukan --data /data/physionet --keluaran app/ai/artefak/model_rf.joblib
"""

import argparse
import json
import math
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from app.ai.registry import FITUR_MODEL, LEVEL_AMBANG

# Nama kolom PhysioNet untuk setiap fitur model. Fitur turunan (map bila kosong, shock_index) dihitung terpisah.
KOLOM_PHYSIONET = {
    "nadi": "HR",
    "saturasi": "O2Sat",
    "suhu": "Temp",
    "td_sistolik": "SBP",
    "td_diastolik": "DBP",
    "map": "MAP",
    "laju_napas": "Resp",
    "laktat": "Lactate",
    "kreatinin": "Creatinine",
    "trombosit": "Platelets",
    "leukosit": "WBC",
    "bilirubin": "Bilirubin_total",
    "usia": "Age",
    "jenis_kelamin": "Gender",
}
KOLOM_LABEL = "SepsisLabel"
# Persentase pasien stabil (label 0) yang masuk tiap level. Sisanya, 3% teratas, menjadi Kritis.
# Ambang dipilih dari sisi pasien stabil supaya alarm palsu di ruang ICU tetap terbatas.
KUANTIL_NEGATIF = {"sedang": 0.70, "tinggi": 0.90, "kritis": 0.97}
VERSI = "rf-icu-physionet2019-v1"


class DataTidakSesuaiError(ValueError):
    """Berkas PhysioNet tidak punya kolom yang dibutuhkan."""


@dataclass(frozen=True)
class Parameter:
    pohon: int = 150
    kedalaman: int = 10
    daun_minimum: int = 50
    rasio_negatif: float = 0.15
    porsi_uji: float = 0.2
    seed: int = 2019


def fitur_dari_physionet(df: pd.DataFrame) -> pd.DataFrame:
    """Mengubah baris per jam satu pasien menjadi fitur model.

    Nilai terakhir yang diketahui dibawa ke jam berikutnya (forward fill), seperti perawat yang melihat hasil
    lab terakhir. MAP yang kosong dihitung dari sistolik dan diastolik, sama dengan backend.
    """
    kurang = [k for k in [*KOLOM_PHYSIONET.values(), KOLOM_LABEL] if k not in df.columns]
    if kurang:
        raise DataTidakSesuaiError(f"Kolom {kurang} tidak ada di data PhysioNet.")
    isi = df[list(KOLOM_PHYSIONET.values())].ffill()
    hasil = pd.DataFrame({fitur: isi[kolom].astype(float) for fitur, kolom in KOLOM_PHYSIONET.items()})
    map_hitung = (hasil["td_sistolik"] + 2 * hasil["td_diastolik"]) / 3
    hasil["map"] = hasil["map"].fillna(map_hitung)
    sistolik = hasil["td_sistolik"].where(hasil["td_sistolik"] > 0)
    hasil["shock_index"] = hasil["nadi"] / sistolik
    hasil["label"] = df[KOLOM_LABEL].astype(int)
    # Jam tanpa satu pun tanda vital belum bisa dinilai, jadi tidak dipakai.
    ada_vital = hasil[["nadi", "saturasi", "td_sistolik", "laju_napas"]].notna().any(axis=1)
    return hasil.loc[ada_vital, [*FITUR_MODEL, "label"]]


def baca_pasien(path: Path, rasio_negatif: float, seed: int) -> pd.DataFrame:
    """Membaca satu berkas .psv. Semua jam berlabel 1 diambil, jam berlabel 0 diambil sebagian secara acak."""
    fitur = fitur_dari_physionet(pd.read_csv(path, sep="|"))
    acak = np.random.default_rng([seed, int(path.stem.lstrip("p") or 0)])
    pilih = (fitur["label"] == 1) | (acak.random(len(fitur)) < rasio_negatif)
    hasil = fitur.loc[pilih].copy()
    hasil["pasien"] = path.stem
    return hasil


def _baca_semua(berkas: list[Path], rasio_negatif: float, seed: int, proses: int) -> pd.DataFrame:
    if proses <= 1:
        bagian = [baca_pasien(p, rasio_negatif, seed) for p in berkas]
    else:  # pragma: no cover - hanya mempercepat pembacaan 40 ribu berkas
        with ProcessPoolExecutor(max_workers=proses) as pool:
            bagian = list(pool.map(baca_pasien, berkas, [rasio_negatif] * len(berkas), [seed] * len(berkas)))
    return pd.concat(bagian, ignore_index=True)


def bagi_pasien(berkas: list[Path], porsi_uji: float, seed: int) -> tuple[list[Path], list[Path]]:
    """Membagi per pasien, bukan per baris, supaya jam-jam dari pasien yang sama tidak bocor ke data uji."""
    urut = sorted(berkas)
    acak = np.random.default_rng(seed)
    indeks = acak.permutation(len(urut))
    jumlah_uji = max(1, round(len(urut) * porsi_uji))
    uji = {int(i) for i in indeks[:jumlah_uji]}
    return [p for i, p in enumerate(urut) if i not in uji], [p for i, p in enumerate(urut) if i in uji]


def buat_pipeline(param: Parameter) -> Any:
    from sklearn.compose import ColumnTransformer
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import Pipeline

    prep = ColumnTransformer(
        # keep_empty_features: kolom lab yang kosong semua di data latih tetap ada, supaya urutan fitur tidak bergeser.
        [("num", SimpleImputer(strategy="median", keep_empty_features=True), list(FITUR_MODEL))],
        verbose_feature_names_out=False,
    )
    rf = RandomForestClassifier(
        n_estimators=param.pohon,
        max_depth=param.kedalaman,
        min_samples_leaf=param.daun_minimum,
        class_weight="balanced_subsample",
        n_jobs=-1,
        random_state=param.seed,
    )
    return Pipeline([("prep", prep), ("model", rf)])


def pilih_ambang(peluang_negatif: np.ndarray) -> dict[str, float]:
    """Ambang peluang tiap level dari kuantil peluang pasien stabil (lihat KUANTIL_NEGATIF)."""
    ambang = {level: round(float(np.quantile(peluang_negatif, q)), 4) for level, q in KUANTIL_NEGATIF.items()}
    if not ambang["sedang"] <= ambang["tinggi"] <= ambang["kritis"]:  # pragma: no cover - kuantil selalu urut
        raise ValueError("Ambang level tidak urut.")
    return ambang


def level_dari_peluang(peluang: np.ndarray, ambang: dict[str, float]) -> np.ndarray:
    """0 rendah, 1 sedang, 2 tinggi, 3 kritis."""
    level = np.zeros(len(peluang), dtype=int)
    for i, nama in enumerate(LEVEL_AMBANG, start=1):
        level[peluang >= ambang[nama]] = i
    return level


def evaluasi(y: np.ndarray, peluang: np.ndarray, ambang: dict[str, float]) -> dict[str, Any]:
    from sklearn.metrics import average_precision_score, roc_auc_score

    level = level_dari_peluang(peluang, ambang)
    per_level = {}
    for i, nama in enumerate(("rendah", *LEVEL_AMBANG)):
        pilih = level == i
        per_level[nama] = {
            "jumlah_jam": int(pilih.sum()),
            "persen_berlabel_1": round(float(y[pilih].mean() * 100), 2) if pilih.any() else None,
        }
    positif = y == 1
    sensitivitas = {
        f"minimal_{nama}": round(float((level[positif] >= i).mean() * 100), 1) if positif.any() else None
        for i, nama in enumerate(LEVEL_AMBANG, start=1)
    }
    return {
        "auroc": round(float(roc_auc_score(y, peluang)), 4),
        "auprc": round(float(average_precision_score(y, peluang)), 4),
        "prevalensi_persen": round(float(y.mean() * 100), 2),
        "per_level": per_level,
        "sensitivitas_persen": sensitivitas,
    }


def latih(folder: Path, param: Parameter, proses: int = 1, batas_pasien: int | None = None) -> dict[str, Any]:
    berkas = sorted(Path(folder).rglob("*.psv"))
    if batas_pasien:
        berkas = berkas[:batas_pasien]
    if len(berkas) < 2:
        raise DataTidakSesuaiError(f"Berkas .psv di {folder} kurang dari dua.")
    latih_berkas, uji_berkas = bagi_pasien(berkas, param.porsi_uji, param.seed)

    data_latih = _baca_semua(latih_berkas, param.rasio_negatif, param.seed, proses)
    # Data uji dibaca utuh (rasio 1) supaya metrik mencerminkan prevalensi sebenarnya di ICU.
    data_uji = _baca_semua(uji_berkas, 1.0, param.seed, proses)

    pipeline = buat_pipeline(param)
    pipeline.fit(data_latih[list(FITUR_MODEL)], data_latih["label"])
    if list(pipeline.named_steps["model"].classes_) != [0, 1]:
        raise DataTidakSesuaiError("Data latih harus berisi label 0 dan 1.")

    # Ambang dipilih dari data latih, lalu diuji di pasien yang tidak pernah dilihat model.
    peluang_latih = pipeline.predict_proba(data_latih[list(FITUR_MODEL)])[:, 1]
    ambang = pilih_ambang(peluang_latih[data_latih["label"].to_numpy() == 0])
    peluang_uji = pipeline.predict_proba(data_uji[list(FITUR_MODEL)])[:, 1]

    rf = pipeline.named_steps["model"]
    pentingnya = sorted(zip(FITUR_MODEL, rf.feature_importances_, strict=True), key=lambda item: item[1], reverse=True)
    laporan = {
        "versi": VERSI,
        "sumber_data": "PhysioNet/CinC Challenge 2019 (training set A dan B), lisensi CC BY 4.0",
        "label": "SepsisLabel: 1 mulai 6 jam sebelum sepsis terdiagnosis",
        "jumlah_pasien": {"latih": len(latih_berkas), "uji": len(uji_berkas)},
        "jumlah_jam": {"latih": len(data_latih), "uji": len(data_uji)},
        "parameter": param.__dict__,
        "ambang": ambang,
        "uji": evaluasi(data_uji["label"].to_numpy(), peluang_uji, ambang),
        "pentingnya_fitur": {nama: round(float(nilai), 4) for nama, nilai in pentingnya},
    }
    bundle = {
        "model": pipeline,
        "fitur": list(FITUR_MODEL),
        "ambang": ambang,
        "versi": VERSI,
        "laporan": laporan,
    }
    return {"bundle": bundle, "laporan": laporan}


def simpan(hasil: dict[str, Any], keluaran: Path, laporan: Path | None) -> None:
    import joblib

    keluaran.parent.mkdir(parents=True, exist_ok=True)
    rf = hasil["bundle"]["model"].named_steps["model"]
    # Satu thread saat dipakai backend; n_jobs=-1 hanya berguna saat pelatihan.
    rf.set_params(n_jobs=1)
    joblib.dump(hasil["bundle"], keluaran, compress=3)
    if laporan:
        laporan.write_text(json.dumps(hasil["laporan"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def argumen(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Latih model peluang perburukan pasien ICU (PhysioNet 2019).")
    parser.add_argument("--data", type=Path, required=True, help="Folder berisi berkas p*.psv")
    parser.add_argument("--keluaran", type=Path, default=Path("app/ai/artefak/model_rf.joblib"))
    parser.add_argument("--laporan", type=Path, default=Path("ai_training/laporan_model_icu.json"))
    parser.add_argument("--proses", type=int, default=4)
    parser.add_argument("--batas-pasien", type=int, default=None)
    return parser.parse_args(argv)


if __name__ == "__main__":  # pragma: no cover
    a = argumen()
    hasil = latih(a.data, Parameter(), proses=a.proses, batas_pasien=a.batas_pasien)
    simpan(hasil, a.keluaran, a.laporan)
    uji = hasil["laporan"]["uji"]
    print(f"AUROC {uji['auroc']}, AUPRC {uji['auprc']}, ambang {hasil['laporan']['ambang']}")
    print(f"Model: {a.keluaran} ({math.ceil(a.keluaran.stat().st_size / 1e6)} MB)")
