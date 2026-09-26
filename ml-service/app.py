"""Layanan klasifikasi SmartTriage AI.

Membungkus model Random Forest 4 level (rendah/sedang/tinggi/kritis) yang sudah
dilatih dan dievaluasi di notebooks/02_baseline.ipynb, dipanggil dari aplikasi
Next.js (lib/ml-client.ts) menggantikan/mendampingi lib/classify.ts.

Jalankan lokal:
    uvicorn app:app --reload --port 8000
Endpoint:
    GET  /health    -> cek layanan hidup + versi model
    POST /classify  -> { riskLevel, probabilitas, penjelasanAi, faktorUtama, modelVersion }
"""
import warnings
from typing import Optional

import joblib
import numpy as np
import pandas as pd
import shap
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

warnings.filterwarnings("ignore")

# ============================== muat model ==============================
BUNDLE = joblib.load("model_bundle.joblib")
MODEL = BUNDLE["model"]
FITUR = BUNDLE["fitur"]
URUTAN = BUNDLE["urutan_level"]  # ["rendah", "sedang", "tinggi", "kritis"]
KATEGORI_DIKENAL = set(BUNDLE["kategori_keluhan_dikenal"])
VERSI_MODEL = BUNDLE["versi"]

PREP = MODEL.named_steps["prep"]
RF = MODEL.named_steps["model"]
NAMA_FITUR_TRANSFORMASI = PREP.get_feature_names_out()
EXPLAINER = shap.TreeExplainer(RF)

LABEL_INDO = {
    "Sex": "jenis kelamin", "Age": "usia", "Mental": "tingkat kesadaran",
    "NRS_pain": "skala nyeri", "SBP": "tekanan darah sistolik", "DBP": "tekanan darah diastolik",
    "HR": "nadi", "RR": "laju napas", "BT": "suhu tubuh", "Saturation": "saturasi oksigen",
    "map": "tekanan arteri rata-rata (MAP)", "shock_index": "shock index",
}


def label_fitur(nama_transformasi: str) -> str:
    if nama_transformasi.startswith("kategori__kategori_keluhan_"):
        nilai = nama_transformasi.split("kategori_keluhan_", 1)[1]
        return f"kategori keluhan ({nilai})"
    dasar = nama_transformasi.split("__", 1)[-1]
    return LABEL_INDO.get(dasar, dasar)


# ============================== skema request/response ==============================
class PermintaanTriase(BaseModel):
    # tanda vital: SELALU tersedia dari form yang sudah ada (TriageInputSchema.tandaVital)
    SBP: float = Field(..., ge=0, le=320, description="Tekanan darah sistolik (mmHg)")
    DBP: float = Field(..., ge=0, le=200, description="Tekanan darah diastolik (mmHg)")
    HR: float = Field(..., ge=0, le=300, description="Nadi (kali/menit)")
    RR: float = Field(..., ge=0, le=80, description="Laju napas (kali/menit)")
    BT: float = Field(..., ge=20, le=45, description="Suhu tubuh (°C)")
    Saturation: float = Field(..., ge=0, le=100, description="Saturasi oksigen (%)")

    # opsional: usia/jenis kelamin (dari data Pasien, kadang belum lengkap),
    # dan tiga isian baru (skala nyeri, tingkat kesadaran, kategori keluhan) yang
    # belum ada di form -- diisi null sampai formnya diperbarui, model tetap
    # jalan dengan imputasi median/modus seperti yang sudah dites di notebook.
    Age: Optional[float] = Field(None, ge=0, le=120)
    Sex: Optional[int] = Field(None, description="1 = perempuan, 2 = laki-laki")
    Mental: Optional[int] = Field(None, ge=1, le=4, description="1=sadar penuh .. 4=tidak respons (AVPU)")
    NRS_pain: Optional[float] = Field(None, ge=0, le=10, description="Skala nyeri 0-10")
    kategori_keluhan: Optional[str] = Field(None, description="Salah satu kategori dari daftar training")

    gejala: Optional[str] = Field(None, description="Uraian gejala bebas, untuk log saja, tidak dipakai model")


class ResponTriase(BaseModel):
    riskLevel: str
    probabilitas: dict[str, float]
    penjelasanAi: str
    faktorUtama: list[str]
    modelVersion: str


app = FastAPI(title="SmartTriage AI - Layanan Klasifikasi", version=VERSI_MODEL)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ganti dengan domain Vercel spesifik saat deploy produksi
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "modelVersion": VERSI_MODEL, "jumlahFitur": len(FITUR)}


@app.post("/classify", response_model=ResponTriase)
def classify(permintaan: PermintaanTriase):
    data = permintaan.model_dump()
    kategori = data.get("kategori_keluhan")
    if kategori not in KATEGORI_DIKENAL:
        kategori = "Lainnya"  # kategori tak dikenal/kosong -> jatuh ke kategori umum, bukan error

    baris = {
        "Sex": data.get("Sex"), "Age": data.get("Age"), "kategori_keluhan": kategori,
        "Mental": data.get("Mental"), "NRS_pain": data.get("NRS_pain"),
        "SBP": data["SBP"], "DBP": data["DBP"], "HR": data["HR"], "RR": data["RR"],
        "BT": data["BT"], "Saturation": data["Saturation"],
    }
    baris["map"] = (baris["SBP"] + 2 * baris["DBP"]) / 3
    baris["shock_index"] = (baris["HR"] / baris["SBP"]) if baris["SBP"] else None

    try:
        df = pd.DataFrame([baris])[FITUR]
        X_trans = PREP.transform(df)
        if hasattr(X_trans, "toarray"):
            X_trans = X_trans.toarray()

        proba = RF.predict_proba(X_trans)[0]
        idx_pred = int(np.argmax(proba))
        level = URUTAN[idx_pred]

        sv = np.asarray(EXPLAINER.shap_values(X_trans))
        sv_baris = sv[0] if sv.ndim == 3 else np.stack([s[0] for s in sv], axis=-1)
        kontribusi = sv_baris[:, idx_pred]
        nilai_baris = X_trans[0]
        layak = [i for i in range(len(kontribusi))
                 if not (NAMA_FITUR_TRANSFORMASI[i].startswith("kategori__") and nilai_baris[i] == 0)]
        urutan_idx = sorted(layak, key=lambda i: -abs(kontribusi[i]))[:3]
        faktor = [
            f"{label_fitur(NAMA_FITUR_TRANSFORMASI[i])} "
            f"({'meningkatkan' if kontribusi[i] > 0 else 'menurunkan'} kemungkinan level ini)"
            for i in urutan_idx
        ]
    except Exception as exc:  # pragma: no cover - dijaga supaya Next.js selalu dapat error jelas, bukan 500 polos
        raise HTTPException(status_code=422, detail=f"Gagal memproses data triase: {exc}") from exc

    dasar = "; ".join(faktor) if faktor else "tidak ada faktor tunggal yang menonjol"
    penjelasan = (
        f'Model machine learning (Random Forest, {VERSI_MODEL}) merekomendasikan risk level '
        f'"{level.upper()}". Faktor paling berpengaruh pada prediksi ini: {dasar}. '
        "Rekomendasi ini bersifat bantu-keputusan (explainable AI, bukan Generative AI) dan wajib "
        "divalidasi oleh tenaga medis (human-in-the-loop) sebelum digunakan sebagai acuan akhir."
    )

    return ResponTriase(
        riskLevel=level,
        probabilitas={lvl: round(float(p), 4) for lvl, p in zip(URUTAN, proba)},
        penjelasanAi=penjelasan,
        faktorUtama=faktor,
        modelVersion=VERSI_MODEL,
    )
