# Backend SmartTriage AI

Backend Flask untuk aplikasi mobile perawat dan dokter (Flutter) serta web admin dan halaman Eir (React).
Rancangannya mengikuti Desain Arsitektur Backend v2.0 dan SKPL v3.0. Semua endpoint ada di bawah `/api/v1`.

Yang sudah dikerjakan:

- Tahap 1: struktur aplikasi, delapan tabel beserta migrasi awal, autentikasi (login, refresh, logout, profil),
  RBAC tiga peran, format error Problem Details, dan health check.
- Tahap 2a: pencarian pasien, registrasi kunjungan, input triase dengan rekomendasi risk level (Random Forest +
  SHAP, dengan aturan cadangan), detail triase, serta konfigurasi triase untuk admin.

## Kebutuhan

- Python 3.12
- PostgreSQL 16 (paling mudah lewat Docker Compose di folder ini)

## Menjalankan di lokal

```bash
cd backend
cp .env.example .env            # isi rahasia, password basis data, dan password akun demo
docker compose up -d db         # PostgreSQL 16 + role smarttriage_app

python3.12 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt

.venv/bin/flask db upgrade      # membuat tabel (dijalankan sebagai role pemilik)
.venv/bin/flask seed-demo       # akun demo admin, perawat, dan dokter
.venv/bin/flask seed-demo --dengan-pasien   # opsional: pasien, kunjungan, dan triase simulasi
.venv/bin/flask run --debug     # http://127.0.0.1:5000/api/v1/health
```

Dengan `APP_ENV=development`, dokumentasi API bisa dibuka di `http://127.0.0.1:5000/api/v1/openapi/swagger`.
Spesifikasi OpenAPI untuk membangkitkan klien Dart bisa diekspor dengan `.venv/bin/flask openapi -o openapi.json`.

### Dua role basis data

Aplikasi berjalan sebagai `smarttriage_app` (`DATABASE_URL`), sedangkan migrasi dijalankan oleh pemilik skema
(`DATABASE_URL_MIGRASI`). Role aplikasi hanya boleh membaca dan menambah baris `log_audit`, tidak boleh mengubah
atau menghapusnya, sesuai NFR-06. Hak aksesnya diberikan oleh migrasi awal, jadi role `smarttriage_app` harus sudah
ada sebelum `flask db upgrade` dijalankan; bila belum ada, migrasi berhenti dengan pesan error. Di Docker Compose role
ini dibuat oleh `docker/initdb/10-role-aplikasi.sh`.

`GET /api/v1/health` ikut memeriksa hal ini. Bila aplikasi ternyata terhubung dengan role yang masih bisa mengubah
`log_audit` (misalnya `DATABASE_URL` terisi role pemilik), komponen `hak_akses_log_audit` bernilai `gagal` dan health
check membalas 503.

## Endpoint Tahap 2a

| Endpoint | Peran | Keterangan |
|---|---|---|
| `GET /api/v1/pasien?q=` | perawat, dokter | Cari pasien lama dari potongan nama atau NIK lengkap 16 digit, maksimal 20 hasil |
| `POST /api/v1/kunjungan` | perawat | Registrasi singkat; pilih pasien lama lewat `id_pasien` atau isi identitas pasien baru |
| `POST /api/v1/kunjungan/{id}/triase` | perawat | Simpan triase beserta rekomendasi risk level, tiga faktor penjelas, dan peringatan tanda vital |
| `GET /api/v1/triase/{id}` | perawat, dokter | Detail triase dalam bentuk yang sama dengan respons POST |
| `GET /api/v1/admin/konfigurasi` | admin | Ambang aturan cadangan, batas waktu tunggu, ambang keyakinan, dan versi model |
| `PATCH /api/v1/admin/konfigurasi` | admin | Ubah sebagian konfigurasi; setiap perubahan masuk log audit |

### Model triase

Bundle Random Forest dari prototipe disalin ke `app/ai/artefak/model_rf.joblib` dan dimuat sekali saat aplikasi
start, bersama explainer SHAP. Bila berkas itu tidak ada atau rusak, aplikasi tetap berjalan: rekomendasi diambil
dari aturan cadangan (`sumber_rekomendasi = "aturan"`) dan komponen `model_triase` di health check bernilai `gagal`
dengan status keseluruhan `degraded`. Lokasinya bisa diganti lewat `MODEL_RF_PATH`.

Konfigurasi triase disimpan di memori proses selama 60 detik. Perubahan lewat PATCH langsung berlaku di worker
yang memprosesnya; worker Gunicorn lain menyesuaikan paling lambat 60 detik kemudian.

## Akun demo

`flask seed-demo` membuat tiga akun dengan password dari `.env`:

| Peran   | Email                      | Variabel password       |
|---------|----------------------------|-------------------------|
| Admin   | admin@smarttriage.demo     | `SEED_PASSWORD_ADMIN`   |
| Perawat | perawat@smarttriage.demo   | `SEED_PASSWORD_PERAWAT` |
| Dokter  | dokter@smarttriage.demo    | `SEED_PASSWORD_DOKTER`  |

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

## Dependensi

Versi dependensi dikunci di `requirements.txt` dan `requirements-dev.txt`. Untuk menambah atau memperbarui paket,
ubah `requirements.in` atau `requirements-dev.in`, lalu bangkitkan ulang:

```bash
uv pip compile requirements.in -o requirements.txt --python-version 3.12
uv pip compile requirements-dev.in -o requirements-dev.txt --python-version 3.12
```
