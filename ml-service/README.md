# SmartTriage AI — Layanan Klasifikasi (ml-service)

Layanan FastAPI yang membungkus model Random Forest 4 level (rendah/sedang/tinggi/kritis)
yang sudah dilatih dan dievaluasi di `notebooks/02_baseline.ipynb` dan Dokumen Project
Framing (macro-F1 0,729 pada data uji). Ini **bukan LLM/Generative AI** — modelnya adalah
Random Forest biasa dengan penjelasan berbasis SHAP (*explainable ML*), sesuai justifikasi
yang sudah ditulis di dokumen framing.

Dipanggil dari aplikasi Next.js lewat `lib/ml-client.ts`, yang otomatis jatuh ke
`lib/classify.ts` (aturan lama) kalau layanan ini mati atau timeout — jadi triase
**tidak pernah gagal total** hanya karena layanan ML sedang tidak bisa diakses.

## Menjalankan lokal

```bash
pip install -r requirements.txt --break-system-packages   # atau pakai virtualenv
uvicorn app:app --reload --port 8000
```

Cek `http://127.0.0.1:8000/health` — harus muncul `{"status":"ok", ...}`.

Lalu di aplikasi Next.js, buat `.env.local` (lihat `.env.example` di root repo) dan isi:

```
ML_SERVICE_URL=http://127.0.0.1:8000
```

## Melatih ulang model

Kalau `data.csv` (dataset KTAS) atau `triase_data.py` berubah, latih ulang dengan:

```bash
python latih_model.py
```

Ini akan mencetak metrik pada data uji (harus mendekati yang sudah dilaporkan di
Dokumen Project Framing: macro-F1 ~0,73) lalu menyimpan `model_bundle.joblib` yang
baru — file ini yang dibaca `app.py` saat startup.

## Endpoint

- `GET /health` — cek layanan hidup dan versi model.
- `POST /classify` — body JSON berisi tanda vital (wajib: `SBP, DBP, HR, RR, BT, Saturation`)
  ditambah field opsional (`Age, Sex, Mental, NRS_pain, kategori_keluhan`). Field opsional
  yang kosong akan diisi otomatis oleh model (median/modus), sama seperti yang sudah
  diuji di notebook. Lihat `app.py` untuk detail skema request/response.

## Deployment (produksi)

**Vercel tidak cocok untuk layanan ini** — serverless function Vercel tidak didesain untuk
proses yang menahan model scikit-learn + SHAP explainer di memori antar-request, dan ukuran
dependensinya (scikit-learn, shap, pandas) kemungkinan melebihi batas serverless function.
Deploy layanan ini secara TERPISAH dari aplikasi Next.js, misalnya di:

- **Render** (render.com) — free tier tersedia, cukup hubungkan folder ini sebagai Web Service,
  build command `pip install -r requirements.txt`, start command `uvicorn app:app --host 0.0.0.0 --port $PORT`.
- **Railway** (railway.app) — serupa, deploy dari GitHub langsung.
- **Fly.io** — perlu Dockerfile sederhana (belum disertakan di sini).

Setelah dapat URL publiknya (misalnya `https://smarttriage-ml.onrender.com`), isi
`ML_SERVICE_URL` di **Vercel** (Settings → Environment Variables) dengan URL itu, lalu
redeploy aplikasi Next.js-nya.

Ganti juga `allow_origins=["*"]` di `app.py` (CORS) dengan domain Vercel yang sebenarnya
sebelum benar-benar dipakai publik.

## Isi folder

- `app.py` — layanan FastAPI (endpoint `/health` dan `/classify`).
- `latih_model.py` — skrip melatih ulang model dari `data.csv`.
- `triase_data.py` — modul pembersihan data & fitur (sama dengan yang dipakai di notebooks).
- `model_bundle.joblib` — model terlatih + metadata (fitur, urutan level, versi).
- `data.csv` — dataset KTAS (Kaggle, sumber Moon dkk. 2019) untuk latih ulang. **Jangan
  commit ke repo publik** — lisensinya belum sepenuhnya jelas (lihat catatan sebelumnya).
