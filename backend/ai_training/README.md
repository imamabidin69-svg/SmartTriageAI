# Pelatihan model AI SmartTriage ICU

Folder ini berisi tiga hal:

1. Model peluang perburukan pasien ICU (Random Forest + SHAP) dari data PhysioNet 2019. Bagian A.
2. Evaluasi Eir untuk keluarga pasien ICU. Bagian B.
3. Pembaca layar alat (YOLO digit 0-9) dari enam dataset Roboflow Universe. Bagian C.

## A. Model peluang perburukan (`perburukan.py`)

Data: PhysioNet/Computing in Cardiology Challenge 2019, 40.336 pasien ICU dari dua rumah sakit, satu baris
per jam, lisensi CC BY 4.0 (https://physionet.org/content/challenge-2019/1.0.0/). Label `SepsisLabel` bernilai
1 mulai 6 jam sebelum sepsis terdiagnosis, jadi dipakai sebagai label "pasien akan memburuk dalam 6 jam".

Fitur yang dipakai hanya yang bisa dicatat perawat di samping bed: nadi, saturasi, suhu, tekanan darah sistolik
dan diastolik, MAP, laju napas, laktat, kreatinin, trombosit, leukosit, bilirubin total, usia, jenis kelamin,
dan shock index. Hasil lab boleh kosong; nilai kosong diisi median oleh imputer di dalam pipeline.

Mengunduh data (sekitar 40 ribu berkas kecil, kurang lebih 250 MB) dari bucket terbuka PhysioNet:

```bash
aws s3 sync --no-sign-request s3://physionet-open/challenge-2019/1.0.0/training/ data/physionet
```

Melatih dan menyimpan model ke `app/ai/artefak/model_rf.joblib`, beserta laporan evaluasi:

```bash
python -m ai_training.perburukan --data data/physionet --keluaran app/ai/artefak/model_rf.joblib \
    --laporan ai_training/laporan_model_icu.json
```

Data dibagi per pasien (80% latih, 20% uji) supaya jam-jam dari pasien yang sama tidak bocor ke data uji.
Ambang level dipilih dari peluang pasien stabil di data latih: 70% pasien stabil berada di Rendah, 20% di Sedang,
7% di Tinggi, dan 3% teratas di Kritis. Hasil versi `rf-icu-physionet2019-v1` (lihat `laporan_model_icu.json`):

| Ukuran | Nilai |
| --- | --- |
| AUROC pada 8.067 pasien uji | 0,736 |
| Persen jam berlabel memburuk: Rendah, Sedang, Tinggi, Kritis | 0,9%, 2,7%, 4,6%, 7,5% |
| Prevalensi jam berlabel memburuk | 1,75% |

Angka AUROC ini wajar untuk fitur satu waktu tanpa tren; pemenang challenge memakai fitur tren berjam-jam.
Karena itu di aplikasi model tidak dipakai sendirian: level akhir adalah yang lebih tinggi antara NEWS2 dan
model, dan setiap kenaikan level tetap harus disetujui dokter.

## B. Evaluasi Eir (`evaluasi_eir.py`)

```bash
python -m ai_training.evaluasi_eir
```

Memakai 30 kalimat keluarga pasien yang disusun sendiri (belum ada dataset terbuka berbahasa Indonesia).
Hasil saat ini: Recall@3 panduan 0,97 (target 0,86), informasi penting recall 1,00 dan presisi 1,00.

## C. Pembaca layar alat (YOLO)

Skrip di bawah menyiapkan model YOLO yang dipakai `POST /api/v1/pemindaian` untuk membaca angka di
layar alat. Hasilnya diekspor ke ONNX supaya backend cukup memakai onnxruntime tanpa PyTorch.

### C0. Model yang sudah terpasang

`app/ai/artefak/yolo_digit.onnx` (versi `yolo11n-digit-v1`) dilatih dari enam dataset Roboflow Universe
berlisensi CC BY 4.0: 3.514 foto latih, 458 validasi, dan 80 uji. Rinciannya ada di `laporan_model_yolo.json`.

| Ukuran | Hasil |
|---|---|
| Validasi mAP50 / mAP50-95 | 0,993 / 0,901 |
| Uji lewat jalur backend: digit (presisi / recall) | 0,938 / 0,990 |
| Uji lewat jalur backend: angka terbaca tepat | 128 dari 142 (90,1%) |
| Kolom tensimeter terisi dan benar, ambang 0,85 | 23 dari 57 kolom terisi, semuanya benar |
| Kolom tensimeter terisi dan benar, ambang 0,6 | 48 dari 57 kolom terisi, semuanya benar |

Model ini jarang memberi keyakinan di atas 0,85 untuk angka tiga digit, jadi dengan ambang bawaan banyak
kolom sistolik dikosongkan. Turunkan `ambang_keyakinan` menjadi 0,6 lewat halaman Pengaturan di web admin.
Perawat tetap memeriksa angka sebelum menyimpan.

Foto sebaiknya diambil dari dekat sampai layar alat memenuhi bingkai. Pada foto dari jauh, digit LCD terlalu
kecil dan motif kain di latar bisa terbaca sebagai digit.

### C0b. Melatih ulang di laptop dari zip Roboflow

Unduh setiap dataset dari Roboflow Universe dalam format YOLOv8 ("Download zip to computer"), ekstrak
masing-masing ke foldernya sendiri, lalu gabungkan. Nama kelas dipetakan otomatis ke 0-9, kelas lain
(titik, minus, kotak satu angka utuh) dibuang, dan label poligon diubah menjadi kotak.

```bash
python -m ai_training.dataset --sumber data/seven-segments data/bp-device data/bp-digits --tujuan data/gabungan
python -m ai_training.latih --data data/gabungan/data.yaml --epoch 40
python -m ai_training.ekspor --bobot runs/detect/digit_layar/weights/best.pt
```

Tanpa GPU, satu epoch untuk sekitar 3.500 foto memakan waktu kurang lebih 12 menit di CPU empat inti.
Pelatihan juga bisa dijalankan di Google Colab dengan GPU memakai akun Roboflow Anda sendiri.

Cara tercepat: buka `colab_yolo_pembaca_layar.ipynb` di Google Colab (File > Upload notebook), simpan
API key Roboflow di Colab Secrets dengan nama `ROBOFLOW_API_KEY`, isi workspace dan nama proyek, lalu jalankan
sel dari atas. Dataset Roboflow Universe yang memakai nama kelas lain (`seven`, `digit_7`) dipetakan otomatis
ke 0-9, dan kelas yang bukan digit (misalnya `HR` atau `SpO2`) dibuang.

Catatan bedside monitor: tata letak angka di monitor berbeda antar merek, jadi untuk jenis alat
`bedside_monitor` angka hasil deteksi belum dipetakan ke kolom dan perawat mengisinya manual. Tensimeter,
oksimeter, dan termometer sudah dipetakan.

### C1. Dataset

- Foto layar alat dari berbagai sudut dan pencahayaan. Jangan memotret tubuh atau wajah pasien.
- Anotasi di Roboflow: setiap digit 0 sampai 9 satu kotak, dengan nama kelas `0` sampai `9`.
  Titik desimal tidak dianotasi; backend membaca tiga digit termometer, misalnya `368`, sebagai 36,8.
- Bagi menjadi train, valid, dan test. Foto di set test tidak boleh ikut dilatih.
- Ekspor dataset dalam format YOLOv8.

### C2. Menjalankan di Colab

```python
!git clone https://github.com/imamabidin69-svg/SmartTriageAI.git
%cd SmartTriageAI/backend
!pip install -r requirements.txt -r ai_training/requirements-training.txt

# Simpan API key Roboflow di Colab Secrets dengan nama ROBOFLOW_API_KEY, bukan di notebook.
import os
from google.colab import userdata
os.environ["ROBOFLOW_API_KEY"] = userdata.get("ROBOFLOW_API_KEY")

from pathlib import Path
from ai_training.dataset import unduh_dari_roboflow
data_yaml = unduh_dari_roboflow("nama-workspace", "digit-layar-alat", 1, Path("/content/dataset"))

!python -m ai_training.latih --data {data_yaml} --epoch 100
!python -m ai_training.ekspor --bobot runs/detect/digit_layar/weights/best.pt
```

Skrip `latih` memakai bobot awal `yolo11n.pt` dan ukuran gambar 640. Generasi YOLO yang lebih baru
mengekspor ONNX dengan bentuk keluaran berbeda, jadi jangan diganti tanpa menyesuaikan
`app/ai/pembaca_layar.py`.

### C3. Evaluasi (target 95% angka terbaca benar)

Siapkan folder foto uji dan berkas `label.csv` berpemisah titik koma:

```
berkas;jenis_alat;nilai
tensi_001.jpg;tensimeter;td_sistolik=128,td_diastolik=84,nadi=76
oksi_001.jpg;oksimeter;saturasi=97,nadi=82
termo_001.jpg;termometer;suhu=36.8
```

```python
!python -m ai_training.evaluasi --model runs/detect/digit_layar/weights/best.onnx --foto /content/uji --label /content/uji/label.csv
```

Evaluasi memakai penyusun angka dan pemetaan kolom yang sama dengan backend. Skrip keluar dengan kode 1
bila akurasi di bawah 95%.

### C4. Memasang model di backend

Salin `best.onnx` ke `backend/app/ai/artefak/yolo_digit.onnx`, atau atur `MODEL_YOLO_PATH` di `.env`.
Setelah aplikasi dijalankan ulang, `GET /api/v1/health` menampilkan `pembaca_layar: ok`.
