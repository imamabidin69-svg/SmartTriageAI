# Perintah Terminal SmartTriage AI

Kumpulan perintah PowerShell untuk terminal VS Code di Windows. Buka terminal dengan **Ctrl + `**, pastikan jenisnya
PowerShell, lalu salin perintah yang dibutuhkan. Semua contoh menganggap repo ada di
`F:\Kuliah\Matkul\S3\SmartTriageAI`; sesuaikan bila letaknya berbeda.

Baris yang diawali `#` hanya penjelasan dan tidak perlu disalin.

---

## 1. Setiap kali laptop baru dinyalakan

Urutannya: Docker, basis data, backend, lalu web atau mobile.

1. Buka **Docker Desktop** dan tunggu sampai statusnya "Engine running".
2. Terminal pertama untuk backend:

```powershell
cd F:\Kuliah\Matkul\S3\SmartTriageAI\backend
docker compose up -d db
.\.venv\Scripts\Activate.ps1
python -m flask run --debug
```

Backend berjalan di http://127.0.0.1:5000. Biarkan terminal ini terbuka. Untuk menghentikan: **Ctrl + C**.
Perintah Flask harus dijalankan dari folder `backend`; dari folder lain muncul `Could not locate a Flask application`.

Untuk memastikan backend hidup, jalankan di terminal lain (jangan lewat browser, lihat bagian 7):

```powershell
Invoke-RestMethod http://127.0.0.1:5000/api/v1/health    # status harus "ok"
```

Bila aplikasi mobile dijalankan di HP sungguhan (bukan emulator), ganti baris terakhir dengan:

```powershell
python -m flask run --debug --host 0.0.0.0
```

3. Buka terminal kedua (tombol **+** di panel terminal) untuk web atau mobile, lihat bagian 3 dan 4.

---

## 2. Backend (folder `backend`)

Semua perintah di bagian ini dijalankan setelah:

```powershell
cd F:\Kuliah\Matkul\S3\SmartTriageAI\backend
.\.venv\Scripts\Activate.ps1
```

Bila `Activate.ps1` ditolak karena execution policy, jalankan sekali:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### Persiapan pertama (sekali saja)

```powershell
Copy-Item .env.example .env
# isi .env dulu: SECRET_KEY, JWT_SECRET_KEY, password basis data, dan SEED_PASSWORD_*
docker compose up -d db
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m flask db upgrade
python -m flask seed-demo
```

### Basis data

```powershell
docker compose up -d db                  # menyalakan PostgreSQL
docker compose ps                        # cek status container
docker compose stop db                   # mematikan PostgreSQL (data tetap ada)
python -m flask db upgrade               # menjalankan migrasi terbaru
python -m flask seed-demo                # membuat akun demo admin, perawat, dokter
python -m flask seed-demo --dengan-pasien   # menambah 8 pasien ICU simulasi (bed ICU-1 sampai ICU-8)
```

### Pindah ke versi ICU (sekali saja, setelah pull tahap 7)

Data simulasi IGD yang lama tidak punya nomor bed, jadi basis data dikosongkan lalu diisi ulang. Perintah
`down -v` menghapus volume PostgreSQL beserta semua isinya; role aplikasi dibuat lagi otomatis saat container
menyala.

```powershell
docker compose down -v
docker compose up -d db
python -m flask db upgrade               # menjalankan migrasi 0001 lalu 0002_prioritas_icu
python -m flask seed-demo
python -m flask seed-demo --dengan-pasien
```

Bila tidak ingin menghapus volume, cukup `python -m flask db upgrade`. Pasien lama tetap ada tanpa nomor bed,
dan pasien baru wajib diberi nomor bed.

### Menyamakan password akun demo dengan `.env`

Dipakai bila login ditolak padahal password sudah sesuai `.env`. Ini terjadi kalau akun dibuat sebelum `.env` diisi.

```powershell
python -m flask shell
```

Lalu tempel ini di prompt `>>>`. Baris kosong setelah `for` memang perlu. Tekan Enter sampai keluar.

```python
import os
from sqlalchemy import select
from app.extensions import db
from app.models import Pengguna
for email, kunci in [("admin@smarttriage.demo", "SEED_PASSWORD_ADMIN"), ("perawat@smarttriage.demo", "SEED_PASSWORD_PERAWAT"), ("dokter@smarttriage.demo", "SEED_PASSWORD_DOKTER")]:
    db.session.scalar(select(Pengguna).where(Pengguna.email == email)).atur_password(os.environ[kunci])

db.session.commit()
exit()
```

Akun demo backend: `admin@smarttriage.demo`, `perawat@smarttriage.demo`, `dokter@smarttriage.demo`. Passwordnya
adalah isi `SEED_PASSWORD_ADMIN`, `SEED_PASSWORD_PERAWAT`, dan `SEED_PASSWORD_DOKTER` di `.env`. Akun di README root
(admin1@..., perawat1@...) milik prototipe lama dan tidak berlaku di sini.

### Tes dan lint

```powershell
python -m pytest -q                          # semua tes + coverage (butuh Docker menyala)
python -m pytest -q tests/test_daftar_tunggu.py   # satu berkas tes saja
ruff check .
ruff format --check .
ruff format .                                # merapikan format bila --check gagal
```

### Lain-lain

```powershell
python -m flask --app run openapi -o ..\web\openapi.json -i 2      # ekspor spesifikasi API untuk web
python -m flask --app run openapi -o ..\mobile\openapi.json -i 2   # ekspor spesifikasi API untuk mobile
python -m ai_training.evaluasi_eir                                  # evaluasi Eir (30 kalimat keluarga pasien ICU)
python -m ai_training.perburukan --data D:\data\physionet          # latih ulang model ICU (lihat ai_training/README.md)
```

Dokumentasi API (Swagger): http://127.0.0.1:5000/api/v1/openapi/swagger

---

## 3. Web admin dan Eir (folder `web`)

```powershell
cd F:\Kuliah\Matkul\S3\SmartTriageAI\web
npm ci                      # memasang dependensi (sekali, atau setelah package-lock.json berubah)
npm run dev                 # mode pengembangan: http://localhost:5173
npm run build               # build untuk disajikan Flask: buka http://127.0.0.1:5000/staf
```

Tes dan lint:

```powershell
npm run lint
npm run typecheck
npm run test:coverage
```

Setelah skema backend berubah:

```powershell
npm run api:tipe            # setelah openapi.json diekspor ulang dari backend (bagian 2)
```

---

## 4. Aplikasi mobile Flutter (folder `mobile`)

### Menambahkan Flutter ke Path (sekali saja)

Ganti `F:\Flutter\flutter\bin` bila Flutter diekstrak di tempat lain. Perintah ini juga membuang entri
`C:\flutter\bin` yang keliru bila pernah ditambahkan.

```powershell
$p = [Environment]::GetEnvironmentVariable("Path", "User")
$p = ($p -split ';' | Where-Object { $_ -and $_ -ne 'C:\flutter\bin' -and $_ -ne 'F:\Flutter\flutter\bin' }) -join ';'
[Environment]::SetEnvironmentVariable("Path", "$p;F:\Flutter\flutter\bin", "User")
```

Tutup VS Code sepenuhnya lalu buka lagi, kemudian cek dengan `flutter --version`.

### Memberi tahu lokasi Android SDK (sekali saja)

Lokasi SDK terlihat di Android Studio: Settings > Languages & Frameworks > Android SDK > Android SDK Location.
Ganti `F:\Android-Studio\ASSDK` bila berbeda.

```powershell
flutter config --android-sdk "F:\Android-Studio\ASSDK"
[Environment]::SetEnvironmentVariable("ANDROID_HOME", "F:\Android-Studio\ASSDK", "User")
```

Tutup VS Code lalu buka lagi, kemudian:

```powershell
flutter doctor --android-licenses       # jawab y untuk semua
flutter doctor
```

### Memasang NDK dan CMake (sekali saja)

Build Android butuh **NDK 28.2.13676358** dan **CMake 3.22.1**, karena salah satu dependensi (paket `jni` yang dipakai
`path_provider_android`) mengompilasi kode native. Flutter mencoba memasangnya otomatis, tapi di laptop ini gagal
dengan pesan `Package ndk not found`, jadi pasang lewat Android Studio:

1. Settings > Languages & Frameworks > Android SDK > tab **SDK Tools**.
2. Centang **Show Package Details** di kanan bawah.
3. Di bawah **NDK (Side by side)** centang `28.2.13676358`, di bawah **CMake** centang `3.22.1`.
4. Klik **Apply** dan tunggu unduhan selesai, lalu jalankan `flutter run` lagi.

### Kompilasi Kotlin dan beda drive

Proyek ada di drive F: sedangkan cache pub Flutter ada di drive C:. Kompilasi Kotlin inkremental tidak bisa menangani
berkas di dua drive berbeda dan gagal dengan pesan `this and base files have different roots`. Karena itu
`android\gradle.properties` berisi `kotlin.incremental=false`; jangan dihapus. Build sedikit lebih lama, tapi stabil.
Langkah bila pesan itu masih muncul ada di bagian 7.

### Perintah umum

```powershell
cd F:\Kuliah\Matkul\S3\SmartTriageAI\mobile
flutter doctor              # cek Flutter dan Android toolchain
flutter pub get             # memasang dependensi (sekali, atau setelah pubspec.lock berubah)
flutter devices             # melihat emulator atau HP yang terhubung
```

### Menjalankan di HP lewat kabel USB (disarankan)

`adb reverse` meneruskan port 5000 di HP ke Flask di laptop lewat kabel, jadi tidak perlu WiFi, alamat IP,
`--host 0.0.0.0`, maupun izin firewall. Ulangi `adb reverse` setiap kali kabel dicabut lalu dipasang lagi.

```powershell
$adb = "$env:ANDROID_HOME\platform-tools\adb.exe"
& $adb devices                          # HP harus tampil dengan status "device"
& $adb reverse tcp:5000 tcp:5000
& $adb reverse --list                   # harus tampil baris tcp:5000 tcp:5000
flutter run --dart-define=API_BASE_URL=http://127.0.0.1:5000
```

Pemetaan `adb reverse` juga hilang setiap kali adb dinyalakan ulang, misalnya setelah muncul tulisan
`daemon not running; starting now`. Bila `& $adb reverse --list` kosong, jalankan lagi `& $adb reverse tcp:5000 tcp:5000`.

### Menjalankan di emulator

```powershell
flutter run                 # server otomatis http://10.0.2.2:5000
```

### Menjalankan di HP lewat WiFi

Backend harus jalan dengan `--host 0.0.0.0` (bagian 1). Laptop dan HP harus di WiFi yang sama:

```powershell
ipconfig                    # catat "IPv4 Address" Wi-Fi, misalnya 192.168.1.10
flutter run --dart-define=API_BASE_URL=http://192.168.1.10:5000
```

Saat aplikasi berjalan: tekan **r** untuk hot reload, **R** untuk restart, **q** untuk berhenti.

### Tes dan lint

```powershell
flutter analyze
flutter test --coverage
dart run tool/cek_coverage.dart        # coverage tanpa kode hasil generate, minimal 80%
dart format --line-length 120 lib test # merapikan format
```

Uji kontrak dengan backend sungguhan (backend harus menyala; password dari `.env` backend):

```powershell
flutter test test_backend --dart-define=API_UJI=http://127.0.0.1:5000 --dart-define=PASSWORD_PERAWAT=isi --dart-define=PASSWORD_DOKTER=isi
```

### Build APK

```powershell
flutter build apk --debug --dart-define=API_BASE_URL=http://192.168.1.10:5000
flutter build apk --release --dart-define=API_BASE_URL=https://alamat-railway
```

Hasilnya ada di `mobile\build\app\outputs\flutter-apk\`.

### Setelah skema backend berubah

```powershell
dart run swagger_parser
dart run build_runner build --delete-conflicting-outputs
```

---

## 5. Prototipe Next.js lama (root repo)

```powershell
cd F:\Kuliah\Matkul\S3\SmartTriageAI
npm ci
npm run dev                 # http://localhost:3000
npm run lint
npx tsc --noEmit
npm run test
npm run build
```

---

## 6. Git (dikerjakan sendiri)

```powershell
cd F:\Kuliah\Matkul\S3\SmartTriageAI
git status
git diff
git add backend web mobile PERINTAH-TERMINAL.md README.md
git commit -m "pesan commit"
git push origin main
git log --oneline -5
```

Sebelum `git add`, pastikan `git status` tidak menampilkan `.env`, `.venv`, `node_modules`, `web/dist`,
`mobile/build`, atau `coverage`. Semuanya sudah diabaikan lewat `.gitignore`.

---

## 7. Bila ada masalah

| Gejala | Penyebab dan solusi |
|---|---|
| `flask : The term 'flask' is not recognized` | Venv belum aktif atau beda venv. Jalankan `.\.venv\Scripts\Activate.ps1` di folder `backend`, lalu pakai `python -m flask ...` |
| `Error: Could not locate a Flask application` | Flask dijalankan dari folder lain, misalnya `mobile`. Pindah dulu ke folder `backend`, aktifkan venv, lalu `python -m flask run --debug` |
| Membuka alamat backend di browser malah menampilkan halaman masuk, bukan teks JSON | Bukan tanda backend mati. Alamat yang bukan `/api/...` dijawab aplikasi web, dan browser bisa memakai salinan dari cache PWA. Cek backend dengan `Invoke-RestMethod http://127.0.0.1:5000/api/v1/health` |
| Tampilan web masih tampilan lama setelah `npm run build` | Cache PWA. Tekan Ctrl+Shift+R, atau tutup tab lalu buka lagi |
| Tes backend gagal dengan `ConnectionTimeout` atau `connection refused` | Docker belum menyala. Buka Docker Desktop, lalu `docker compose up -d db` |
| Login web atau mobile ditolak dengan password dari `.env` | Lihat "Menyamakan password akun demo" di bagian 2. Pastikan juga emailnya `@smarttriage.demo` tanpa angka |
| "Terlalu banyak percobaan" saat login | Gagal 5 kali dalam 15 menit. Tunggu 15 menit, atau matikan lalu nyalakan lagi Flask |
| `Address already in use` / port 5000 terpakai | Flask lama masih jalan. Tutup terminalnya, atau `Get-Process python \| Stop-Process` |
| Halaman `/staf` di port 5000 menampilkan "Aplikasi web belum dibangun" | Jalankan `npm run build` di folder `web` |
| Aplikasi mobile: "Tidak dapat terhubung ke server" | Emulator: pastikan Flask menyala. HP: Flask pakai `--host 0.0.0.0`, alamat IP benar, satu WiFi, dan izinkan Python di Windows Defender Firewall untuk jaringan privat |
| `flutter` tidak dikenali | Folder `bin` Flutter belum ada di Path. Lihat "Menambahkan Flutter ke Path" di bagian 4, lalu tutup dan buka ulang VS Code |
| `Unable to locate Android SDK` | Flutter belum tahu lokasi SDK. Lihat "Memberi tahu lokasi Android SDK" di bagian 4 |
| `flutter doctor` minta lisensi Android | `flutter doctor --android-licenses`, lalu tekan `y` untuk semua |
| `flutter devices` tidak menampilkan HP | Aktifkan Opsi pengembang dan Debugging USB di HP, terima pertanyaan "Izinkan debugging USB?", pilih mode USB "Transfer file", coba kabel data lain. Bila masih tidak muncul, pasang Google USB Driver lewat SDK Manager di Android Studio, atau driver USB dari merek HP |
| Aplikasi di HP lewat USB tidak bisa login, "Tidak dapat terhubung ke server" | Kabel sempat dicabut atau adb dinyalakan ulang. Cek `& $adb reverse --list`; bila kosong, jalankan lagi `& $adb reverse tcp:5000 tcp:5000` dan pastikan Flask menyala |
| Build pertama sangat lama atau laptop macet | Normal untuk build pertama (Gradle mengunduh sekitar 1 GB sekali saja). Tutup peramban dan Android Studio selama build |
| Build gagal: `Package ndk not found`, `NDK is not installed`, atau menyebut CMake | Pasang NDK 28.2.13676358 dan CMake 3.22.1 lewat SDK Manager. Lihat "Memasang NDK dan CMake" di bagian 4 |
| Build gagal: `this and base files have different roots` | Pastikan `kotlin.incremental=false` masih ada di `android\gradle.properties`. Lalu di folder `mobile`: `cd android`, `.\gradlew.bat --stop`, `cd ..`, `Remove-Item -Recurse -Force build\image_picker_android\kotlin`, dan `flutter run` lagi |
| Error "different roots" tetap muncul | Pindahkan cache pub ke drive yang sama dengan proyek: `[Environment]::SetEnvironmentVariable("PUB_CACHE", "F:\pub-cache", "User")`, tutup dan buka ulang VS Code, lalu `flutter pub get` |
| Ikon aplikasi di HP masih ikon lama | Launcher menyimpan ikon lama. Copot aplikasi dengan `& $adb uninstall id.smarttriage.mobile`, lalu `flutter run` lagi (perlu login ulang) |
