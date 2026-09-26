"""Melatih model final SmartTriage AI (4 level: rendah/sedang/tinggi/kritis)
dan menyiapkan SHAP explainer, lalu menyimpan semuanya untuk dipakai layanan API.

Konfigurasi model SAMA PERSIS dengan yang sudah dilaporkan di notebooks/02_baseline.ipynb
dan Dokumen Project Framing (Random Forest, macro-F1 ~0,73 pada satu kali split uji),
bukan konfigurasi baru yang belum pernah diuji.
"""
import warnings
warnings.filterwarnings("ignore")

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

import triase_data as td

data = td.tambah_fitur_turunan(td.bersihkan(td.muat_mentah("data.csv")))
FITUR = td.FITUR_LENGKAP
X, y = data[FITUR], data["y"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=td.SEED)

model = Pipeline([
    ("prep", td.buat_praproses(fitur=FITUR)),
    ("model", RandomForestClassifier(
        n_estimators=300, min_samples_leaf=2, class_weight="balanced_subsample",
        random_state=td.SEED, n_jobs=-1)),
])
model.fit(X_train, y_train)

hasil_uji = td.metrik(y_test, model.predict(X_test))
print("Metrik pada data uji (harus cocok dengan yang sudah dilaporkan sebelumnya):")
for k, v in hasil_uji.items():
    print(f"  {k:15} {v:.3f}")

# latih ulang pada SELURUH data (train+test) untuk model yang benar-benar dipakai
# di produksi -- data uji sudah "dibuka" di atas untuk pelaporan, jadi tidak masalah
# memakainya lagi di sini, sama seperti praktik umum "refit on all data" setelah evaluasi.
model_final = Pipeline([
    ("prep", td.buat_praproses(fitur=FITUR)),
    ("model", RandomForestClassifier(
        n_estimators=300, min_samples_leaf=2, class_weight="balanced_subsample",
        random_state=td.SEED, n_jobs=-1)),
])
model_final.fit(X, y)

bundle = {
    "model": model_final,
    "fitur": FITUR,
    "urutan_level": td.URUTAN,         # ["rendah", "sedang", "tinggi", "kritis"]
    "kode_level": td.KODE,             # {"rendah":0, "sedang":1, "tinggi":2, "kritis":3}
    "kategori_keluhan_dikenal": [nama for nama, _ in td.ATURAN_KELUHAN] + ["Lainnya"],
    "metrik_uji": hasil_uji,
    "versi": "smarttriage-rf-v1.0.0",
    "catatan": ("Random Forest, 4 level, dilatih ulang pada seluruh data KTAS (1.267 rekam) "
                "setelah evaluasi pada data uji (lihat metrik_uji). Bukan Gen AI / LLM."),
}
joblib.dump(bundle, "model_bundle.joblib")
print("\nTersimpan: model_bundle.joblib")
print("Fitur:", FITUR)
