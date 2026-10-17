# Pelatihan pembaca layar alat (YOLO)

Skrip di folder ini menyiapkan model YOLO yang dipakai `POST /api/v1/pemindaian` untuk membaca angka di
layar tensimeter, oksimeter, dan termometer digital. Pelatihan dijalankan di Google Colab dengan GPU, lalu
hasilnya diekspor ke ONNX supaya backend cukup memakai onnxruntime tanpa PyTorch.

## 1. Dataset

- Foto layar alat dari berbagai sudut dan pencahayaan. Jangan memotret tubuh atau wajah pasien.
- Anotasi di Roboflow: setiap digit 0 sampai 9 satu kotak, dengan nama kelas `0` sampai `9`.
  Titik desimal tidak dianotasi; backend membaca tiga digit termometer, misalnya `368`, sebagai 36,8.
- Bagi menjadi train, valid, dan test. Foto di set test tidak boleh ikut dilatih.
- Ekspor dataset dalam format YOLOv8.

## 2. Menjalankan di Colab

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

## 3. Evaluasi (target 95% angka terbaca benar)

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

## 4. Memasang model di backend

Salin `best.onnx` ke `backend/app/ai/artefak/yolo_digit.onnx`, atau atur `MODEL_YOLO_PATH` di `.env`.
Setelah aplikasi dijalankan ulang, `GET /api/v1/health` menampilkan `pembaca_layar: ok`.
