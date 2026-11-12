# Backend SmartTriage AI

Backend Flask untuk aplikasi mobile perawat dan dokter (Flutter) serta web admin dan halaman Eir (React).
Rancangannya mengikuti Desain Arsitektur Backend v2.0 dan SKPL v3.0. Semua endpoint ada di bawah `/api/v1`.

Yang sudah dikerjakan:

- Tahap 1: struktur aplikasi, delapan tabel beserta migrasi awal, autentikasi (login, refresh, logout, profil),
  RBAC tiga peran, format error Problem Details, dan health check.
- Tahap 2a: pencarian pasien, registrasi kunjungan, input triase dengan rekomendasi risk level (Random Forest +
  SHAP, dengan aturan cadangan), detail triase, serta konfigurasi triase untuk admin.
- Tahap 2b dan 2c: validasi dan log audit, daftar tunggu, peringatan, kelola staf, riwayat, rekap, dan ekspor CSV.
- Tahap 3: pemindaian layar alat (YOLO ONNX) dan skrip pelatihan di `ai_training/`.
- Tahap 4: asisten anamnesis Eir.
- Tahap 5: SpaRoute yang menyajikan aplikasi web admin dan halaman Eir dari folder `web/` di root repo.
- Tahap 6: penanda `ringkasan_eir_siap` di daftar tunggu untuk aplikasi mobile Flutter di folder `mobile/`.
- Tahap 7 (perubahan lingkup ke ICU): migrasi `0002_prioritas_icu`, skor NEWS2, model peluang perburukan dari
  PhysioNet 2019, persetujuan dokter hanya saat penilaian awal dan saat level naik, papan prioritas ICU dengan
  interval observasi, dan Eir untuk keluarga pasien ICU. Alasan dan rinciannya ada di
  `CATATAN-PERUBAHAN-ICU.md` di root repo.

Kumpulan perintah PowerShell untuk Windows ada di `PERINTAH-TERMINAL.md` di root repo.

## Kebutuhan

- Python 3.12
- PostgreSQL 16 (paling mudah lewat Docker Compose di folder ini)

## Menjalankan di lokal

Linux atau macOS:

```bash
cd backend
cp .env.example .env            # isi rahasia, password basis data, dan password akun demo
docker compose up -d db         # PostgreSQL 16 + role smarttriage_app

python3.12 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt

.venv/bin/flask db upgrade      # membuat tabel (dijalankan sebagai role pemilik)
.venv/bin/flask seed-demo       # akun demo admin, perawat, dan dokter
.venv/bin/flask seed-demo --dengan-pasien   # opsional: 8 bed ICU dengan pasien dan observasi simulasi
.venv/bin/flask run --debug     # http://127.0.0.1:5000/api/v1/health
```

Windows (PowerShell di VS Code). Perintahnya sama, hanya cara memanggil venv yang berbeda. Memanggil lewat
`python -m` menghindari error `'flask' is not recognized`:

```powershell
cd backend
Copy-Item .env.example .env       # isi rahasia, password basis data, dan password akun demo
docker compose up -d db           # Docker Desktop harus sudah menyala

py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1      # bila ditolak: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
python -m pip install -r requirements-dev.txt

python -m flask db upgrade
python -m flask seed-demo
python -m flask run --debug       # tambahkan --host 0.0.0.0 agar bisa dibuka dari HP di WiFi yang sama
```

Dengan `APP_ENV=development`, dokumentasi API bisa dibuka di `http://127.0.0.1:5000/api/v1/openapi/swagger`.
Spesifikasi OpenAPI untuk membangkitkan klien Dart bisa diekspor dengan `.venv/bin/flask openapi -o openapi.json`.

### Aplikasi web (admin dan Eir)

Hasil build aplikasi React di `web/dist` disajikan Flask dari origin yang sama dengan API, sehingga cookie login dan
CSRF tidak perlu pengaturan CORS. Aset ber-hash di `assets/` disimpan lama oleh peramban, sedangkan `index.html` dan
service worker selalu dicek ulang. Alamat lain yang bukan berkas dijawab `index.html` karena rutenya diatur React
Router; alamat di bawah `/api` tetap dijawab Problem Details. Lokasi build bisa diganti lewat `WEB_DIST_PATH`.

```bash
cd ../web && npm ci && npm run build   # lalu buka http://127.0.0.1:5000/staf
```

Saat mengembangkan tampilan, cukup jalankan `npm run dev` di folder `web`; server Vite meneruskan `/api` ke Flask.

### Dua role basis data

Aplikasi berjalan sebagai `smarttriage_app` (`DATABASE_URL`), sedangkan migrasi dijalankan oleh pemilik skema
(`DATABASE_URL_MIGRASI`). Role aplikasi hanya boleh membaca dan menambah baris `log_audit`, tidak boleh mengubah
atau menghapusnya, sesuai NFR-06. Hak aksesnya diberikan oleh migrasi awal, jadi role `smarttriage_app` harus sudah
ada sebelum `flask db upgrade` dijalankan; bila belum ada, migrasi berhenti dengan pesan error. Di Docker Compose role
ini dibuat oleh `docker/initdb/10-role-aplikasi.sh`.

`GET /api/v1/health` ikut memeriksa hal ini. Bila aplikasi ternyata terhubung dengan role yang masih bisa mengubah
`log_audit` (misalnya `DATABASE_URL` terisi role pemilik), komponen `hak_akses_log_audit` bernilai `gagal` dan health
check membalas 503.

## Endpoint alur ICU

Nama endpoint mengikuti SKPL. Di ICU, `kunjungan` adalah satu masa rawat di ICU dan `triase` adalah satu observasi
beserta penilaian prioritasnya.

| Endpoint | Peran | Keterangan |
|---|---|---|
| `GET /api/v1/pasien?q=` | perawat, dokter | Cari pasien lama dari potongan nama atau NIK lengkap 16 digit, maksimal 20 hasil. Pencarian NIK yang tidak ketemu dibatasi 30 kali per 15 menit per akun |
| `POST /api/v1/kunjungan` | perawat | Pasien masuk ICU: nomor bed (wajib, satu bed satu pasien aktif), asal ruangan, diagnosis masuk, dan pasien lama lewat `id_pasien` atau identitas pasien baru |
| `POST /api/v1/kunjungan/{id}/triase` | perawat | Simpan observasi (tanda vital, AVPU, oksigen, lab opsional, ventilator, vasopresor, catatan) beserta skor NEWS2, peluang memburuk, level, dan faktor penjelas |
| `GET /api/v1/triase/{id}` | perawat, dokter | Detail observasi dalam bentuk yang sama dengan respons POST, termasuk level sebelumnya dan status pasien |
| `POST /api/v1/triase/{id}/validasi` | perawat, dokter | Dokter menyetujui atau mengoreksi; perawat hanya mengajukan review; tercatat di log audit |
| `PATCH /api/v1/kunjungan/{id}/status` | dokter | Mulai tindakan (`ditangani`), kembali dipantau (`menunggu`), atau keluar ICU (`selesai`) |
| `GET /api/v1/daftar-tunggu` | perawat, dokter | Papan prioritas ICU yang sudah diurutkan, dengan bed, observasi terakhir, interval observasi, penanda observasi terlambat, persetujuan dokter, dan `ringkasan_eir_siap` |
| `GET /api/v1/peringatan` | perawat, dokter | Penilaian yang menunggu persetujuan dokter, observasi terlambat, dan informasi penting dari Eir |
| `GET /api/v1/pasien/{id}/riwayat` | perawat, dokter | Riwayat observasi pasien dari semua masa rawat, dengan kursor halaman |
| `GET /api/v1/admin/staf` | admin | Daftar staf, filter opsional `peran` dan `aktif` |
| `POST /api/v1/admin/staf` | admin | Tambah staf; password sementara dikirim sekali di respons |
| `PATCH /api/v1/admin/staf/{id}` | admin | Ubah data, aktif/nonaktifkan, atau `atur_ulang_password` |
| `PATCH /api/v1/auth/password` | semua peran | Ganti password sendiri |
| `POST /api/v1/pemindaian` | perawat | Baca angka dari foto layar alat (multipart: `jenis_alat`, `berkas`); foto tidak disimpan |
| `POST /api/v1/kunjungan/{id}/tautan-eir` | perawat | Tautan Eir untuk kode QR (berlaku 2 jam) bagi keluarga pasien yang masih di ICU |
| `GET /api/v1/kunjungan/{id}/ringkasan-eir` | perawat, dokter | Sesi Eir terakhir: ringkasan riwayat dari keluarga, transkrip, dan informasi penting |
| `POST /api/v1/eir/sesi` | pasien/keluarga | Persetujuan dan pembukaan sesi dengan token dari kode QR |
| `POST /api/v1/eir/sesi/{id}/pesan` | pasien/keluarga | Kirim jawaban (header `X-Token-Eir`); dibalas pertanyaan berikutnya atau penutup |
| `POST /api/v1/eir/sesi/{id}/suara` | pasien/keluarga | Jawaban berupa rekaman suara (webm, ogg, mp3, m4a, wav, maksimal 5 MB); rekaman tidak disimpan |
| `POST /api/v1/eir/sesi/{id}/selesai` | pasien/keluarga | Selesaikan sesi setelah minimal 7 jawaban dan buat ringkasan |
| `GET /api/v1/rekap` | admin | Rekap per rentang tanggal; `format=csv` untuk unduhan CSV |
| `GET /api/v1/admin/log-audit` | admin | Log audit dengan filter tanggal, aksi, aktor, dan observasi |
| `GET /api/v1/admin/konfigurasi` | admin | Ambang skor NEWS2, interval observasi per level, ambang keyakinan, dan versi model |
| `PATCH /api/v1/admin/konfigurasi` | admin | Ubah sebagian konfigurasi; setiap perubahan masuk log audit |

### Penilaian prioritas: NEWS2 dan model perburukan

Setiap observasi dihitung skor NEWS2-nya (`app/ai/news2.py`) dari laju napas, saturasi, oksigen tambahan,
sistolik, nadi, kesadaran, dan suhu. Ambang bawaan 7 (Kritis), 5 (Tinggi), dan 3 (Sedang), ditambah aturan satu
parameter bernilai 3 minimal Sedang; ambang bisa diubah admin.

Model Random Forest `rf-icu-physionet2019-v1` (`app/ai/artefak/model_rf.joblib`, dilatih dengan
`ai_training/perburukan.py`) menghitung peluang memburuk dalam 6 jam beserta tiga faktor SHAP terbesar. Level
akhir adalah yang lebih tinggi antara NEWS2 dan model. Bila berkas model tidak ada atau rusak, aplikasi tetap
berjalan dengan NEWS2 saja (`sumber_rekomendasi = "aturan"`), komponen `model_perburukan` di health check bernilai
`gagal`, dan status keseluruhan `degraded`. Lokasinya bisa diganti lewat `MODEL_RF_PATH`.

### Aturan persetujuan dokter

Penilaian awal dan setiap observasi yang levelnya lebih tinggi dari level final terakhir berstatus `menunggu`
dan harus disetujui atau dikoreksi dokter. Observasi yang levelnya sama atau turun langsung berstatus `tercatat`.
Perawat hanya bisa mengajukan review. Koreksi dan ajuan review wajib beralasan minimal 5 karakter. Penilaian yang
sudah final, yang sudah digantikan observasi lebih baru, atau milik pasien yang sudah keluar ICU dibalas 409.

### Pembaca layar alat

Foto layar tensimeter, oksimeter, atau termometer dibaca model YOLO format ONNX
(`app/ai/artefak/yolo_digit.onnx`, bisa diganti lewat `MODEL_YOLO_PATH`). Foto hanya diproses di memori
lalu dibuang. Kolom diisi bila keyakinan model mencapai ambang di konfigurasi (bawaan 0,85) dan nilainya
masuk rentang yang mungkin dicatat; selebihnya dikosongkan untuk diisi manual. Bedside monitor sementara
selalu dikosongkan karena tata letak angkanya berbeda antar merek.

Model YOLO belum ada di repo. Selama itu pemindaian tetap tersimpan dengan semua kolom kosong dan
`GET /api/v1/health` berstatus `degraded`. Untuk mencoba alurnya di development, isi `PEMBACA_LAYAR=tiruan`
di `.env` supaya keluar angka contoh. Cara melatih dan mengekspor model ada di `ai_training/README.md`.

### Eir

Eir menggali riwayat pasien ICU dari keluarganya lewat halaman tanpa akun: kronologi sebelum masuk ICU, riwayat
penyakit, obat rutin, alergi, riwayat operasi, dan kebiasaan. Setiap jawaban diperiksa dulu dengan aturan informasi
penting di `app/ai/eir/informasi_penting.py` tanpa memanggil LLM (misalnya alergi obat, obat pengencer darah,
insulin, kehamilan, alat implan). Bila cocok, labelnya dicatat di sesi dan perawat mendapat peringatan di
`GET /peringatan`, tetapi percakapan tetap berjalan. Tiga panduan paling relevan diambil dengan TF-IDF dari enam
berkas topik di `app/ai/artefak/panduan`, nama dan NIK dibuang dari teks, lalu Groq menyusun satu pertanyaan
berikutnya. Pertanyaan yang berisi diagnosis, perkiraan kondisi, saran obat, atau level diganti pertanyaan inti dari
panduan. Setelah 15 jawaban, atau saat jawaban sudah cukup dan minimal 7, ringkasan dibuat otomatis. Bila Groq tidak
menjawab, respons 503 dan jawaban tetap tersimpan.

Isi panduan dan pola informasi penting masih **draf** dan wajib diperiksa tenaga medis sebelum dipakai di ICU
sungguhan. Untuk mencoba tanpa kunci Groq, isi `LLM_EIR=tiruan` di `.env` (hanya development). Evaluasi pencarian
panduan dan informasi penting dengan 30 kalimat uji:

```bash
python -m ai_training.evaluasi_eir
```

### Akun staf dan password

Admin tidak mengetik password staf. Saat menambah staf atau mengatur ulang password, server membuat password
sementara 12 karakter yang hanya muncul sekali di respons, lalu staf menggantinya lewat `PATCH /auth/password`.
Akun yang dinonaktifkan langsung ditolak di request berikutnya. Setelah password diganti atau diatur ulang, token
yang sudah terbit tetap berlaku sampai kedaluwarsa (access token 15 menit, refresh token 8 jam), karena backend
tidak menyimpan daftar token yang dicabut.

### Rekap dan CSV

Rekap dihitung untuk rentang tanggal WIB (bawaan 7 hari terakhir, maksimal 366 hari). Rata-rata tunggu adalah menit
dari masuk ICU sampai tindakan pertama, dikelompokkan menurut level penilaian terakhir. CSV memakai pemisah titik
koma dan koma desimal supaya langsung terbaca per kolom di Excel berpengaturan Indonesia, berisi agregat saja tanpa
data pasien.

Konfigurasi penilaian disimpan di memori proses selama 60 detik. Perubahan lewat PATCH langsung berlaku di worker
yang memprosesnya; worker Gunicorn lain menyesuaikan paling lambat 60 detik kemudian.

## Akun demo

`flask seed-demo` membuat tiga akun dengan password dari `.env`:

| Peran   | Email                      | Variabel password       |
|---------|----------------------------|-------------------------|
| Admin   | admin@smarttriage.demo     | `SEED_PASSWORD_ADMIN`   |
| Perawat | perawat@smarttriage.demo   | `SEED_PASSWORD_PERAWAT` |
| Dokter  | dokter@smarttriage.demo    | `SEED_PASSWORD_DOKTER`  |

`seed-demo` hanya membuat akun yang belum ada; password akun yang sudah ada tidak diubah. Bila login ditolak padahal
password sudah sesuai `.env`, berarti akun dibuat sebelum `.env` diisi. Samakan lewat `python -m flask shell`
(perintah lengkapnya ada di `PERINTAH-TERMINAL.md`). Akun di README root milik prototipe Next.js lama dan tidak
berlaku di backend ini.

`flask seed-demo --dengan-pasien` menambahkan delapan pasien ICU simulasi di bed ICU-1 sampai ICU-8 (nama fiktif,
tanpa NIK), lengkap dengan diagnosis masuk dan observasi. Isinya mencakup pasien yang belum dinilai, kenaikan level
yang menunggu persetujuan dokter, dan observasi yang levelnya turun, sehingga papan prioritas dan peringatan langsung
bisa dicoba. Karena waktu observasi dibuat mundur dari saat seed dijalankan, pasien akan tampil "observasi terlambat"
bila seed sudah lama dijalankan; jalankan ulang setelah reset basis data untuk data yang segar.

## Autentikasi singkat

- Web admin: `POST /api/v1/auth/login` tanpa header khusus. Token disimpan di cookie HttpOnly. Untuk request
  POST/PATCH, kirim header `X-CSRF-TOKEN` berisi nilai cookie `csrf_access_token`; untuk `/auth/refresh` dan
  `/auth/logout`, pakai nilai cookie `csrf_refresh_token`.
- Aplikasi Flutter: kirim header `X-Client: mobile` saat login. Token ada di body, lalu dikirim lewat
  `Authorization: Bearer <access_token>`. Saat menerima error bertipe `token-kedaluwarsa`, panggil
  `/auth/refresh` dengan refresh token; tipe `sesi-berakhir` berarti harus login ulang.
- Login dibatasi 5 kali gagal dalam 15 menit terakhir, dihitung terpisah per email dan per alamat IP.

## Pengujian dan lint

Tes memakai PostgreSQL sungguhan. Isi `TEST_DATABASE_URL` dan `TEST_DATABASE_URL_MIGRASI` di `.env`; nama
database harus berakhiran `_test` karena database itu dihapus dan dibuat ulang setiap tes dijalankan.

```bash
.venv/bin/pytest                 # termasuk laporan coverage (minimal 80%)
.venv/bin/ruff check .
.venv/bin/ruff format --check .
```

Di Windows dengan venv aktif: `python -m pytest`, `ruff check .`, dan `ruff format --check .`.

## Dependensi

Versi dependensi dikunci di `requirements.txt` dan `requirements-dev.txt`. Untuk menambah atau memperbarui paket,
ubah `requirements.in` atau `requirements-dev.in`, lalu bangkitkan ulang:

```bash
uv pip compile requirements.in -o requirements.txt --python-version 3.12
uv pip compile requirements-dev.in -o requirements-dev.txt --python-version 3.12
```
