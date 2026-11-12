# Aplikasi Mobile SmartTriage AI (perawat dan dokter)

Aplikasi Android yang dibangun dengan Flutter, untuk perawat dan dokter ICU (SKPL v3.0 Tabel 7.1, disesuaikan untuk
ICU; lihat `CATATAN-PERUBAHAN-ICU.md` di root repo). Aplikasi ini
memakai REST API backend Flask yang sama dengan aplikasi web, dengan token Bearer yang disimpan di
`flutter_secure_storage`. Akun admin ditolak di aplikasi ini karena admin memakai aplikasi web.

| Halaman (Tabel 7.1) | Isi |
|---|---|
| Login | Email dan password. Gagal 5 kali dalam 15 menit dibatasi server |
| Prioritas Pasien ICU (pengganti Daftar Tunggu) | Jumlah pasien per level, keterisian bed, kartu pasien berurutan menurut prioritas penanganan dengan nomor urut, bed, diagnosis, skor NEWS2, peluang memburuk, waktu sejak observasi dibanding intervalnya, penanda "Menunggu persetujuan dokter", "Observasi terlambat", "Sedang tindakan", dan "Ringkasan Eir siap", panel peringatan, badge, dan toast. Dimuat ulang tiap 15 detik |
| Pasien Masuk ICU (pengganti Registrasi Singkat) | Tab Pasien Masuk, khusus perawat: nomor bed, asal ruangan, diagnosis masuk, lalu pasien lama atau identitas pasien baru |
| Form Observasi (pengganti Form Triase) | Enam tanda vital dengan tombol Pindai monitor, AVPU, oksigen tambahan, lima hasil lab opsional, ventilator, vasopresor, dan catatan |
| Kamera Pemindaian | Pilih jenis alat, ambil foto dengan kamera bawaan HP, lalu periksa angka terbaca sebelum dipakai. Foto dihapus setelah dikirim |
| Hasil Penilaian (pengganti Hasil dan Penjelasan) | Level prioritas dan perubahannya dari observasi sebelumnya, skor NEWS2 beserta komponennya, peluang memburuk 6 jam dan tiga faktor SHAP, tanda vital, lab, alat bantu. Dokter Setujui atau Koreksi dengan alasan, serta mulai tindakan, kembali dipantau, atau keluar ICU; perawat Ajukan Review |
| Riwayat Observasi Pasien | Tab Riwayat: cari pasien, lalu lihat penilaian awal dan observasinya |
| Profil | Ganti password dan keluar (keputusan M5) |
| Kode QR Eir | Untuk keluarga pasien yang masih di ICU, dibuka dari kartu papan prioritas atau halaman hasil (keputusan M7) |

## Teknologi

Flutter 3.47 (Dart 3.13), Riverpod 3, go_router 18, dio 5, flutter_secure_storage 11, image_picker, qr_flutter.
Klien API dibangkitkan dari spesifikasi OpenAPI backend dengan swagger_parser, json_serializable, dan retrofit.
Semua versi dikunci persis di `pubspec.yaml` dan `pubspec.lock`.

## Tampilan

Aturan tampilan (panduan gaya tahap 6D) sama dengan aplikasi web dan ditulis di `lib/tema.dart`:

- Biru tua `#0F2A4F` dari logo untuk header dan pilihan aktif. Merah, oranye, kuning, dan hijau hanya untuk level
  risiko, mengikuti urutan Manchester Triage System. Hanya Kritis yang berlatar merah penuh; level lain ditandai
  kotak kecil berwarna dan teks, jadi tetap terbaca oleh perawat yang buta warna.
- Daftar dibuat rapat seperti papan pantau ICU: blok putih selebar layar dengan garis tipis, sudut kecil, tanpa
  bayangan dan gradasi. Tombol keputusan di Hasil Penilaian dan tombol Nilai prioritas selalu terlihat di bawah.
- Huruf Atkinson Hyperlegible Next (Braille Institute, lisensi SIL OFL, lihat `assets/fonts/OFL.txt`) disimpan di
  aplikasi, jadi tidak diunduh saat dipakai. Angka memakai angka rata supaya jam dan tanda vital sejajar.
- Logo ada di `assets/logo/logo.png`. Ikon launcher Android ada di `android/app/src/main/res/mipmap-*`, termasuk
  ikon adaptif (`mipmap-anydpi-v26/ic_launcher.xml`) dengan latar putih. Bila ikon lama masih tampil di HP, copot
  aplikasinya dulu lalu jalankan `flutter run` lagi, karena launcher kadang menyimpan ikon lama.

## Persiapan di laptop (sekali saja)

1. Pasang Android Studio versi terbaru dari https://developer.android.com/studio. JDK sudah ikut di dalamnya.
2. Unduh Flutter stable dari https://docs.flutter.dev/get-started/install, ekstrak misalnya ke `C:\flutter`,
   lalu tambahkan `C:\flutter\bin` ke Path (System Properties > Environment Variables), seperti di modul praktikum.
3. Bila Android SDK tidak dipasang di lokasi bawaan, beri tahu lokasinya (lihat Android Studio: Settings >
   Languages & Frameworks > Android SDK), misalnya
   `flutter config --android-sdk "F:\Android-Studio\ASSDK"`, lalu isi variabel `ANDROID_HOME` dengan folder yang sama.
4. Jalankan `flutter doctor --android-licenses`, lalu `flutter doctor` sampai Flutter dan Android toolchain bercentang.
5. Buat emulator di Android Studio (Device Manager), atau siapkan HP Android 8.0 ke atas dengan USB debugging aktif.
6. Di VS Code, pasang ekstensi Flutter dan Dart.

## Menjalankan

Backend harus menyala dulu (lihat `backend/README.md`), lalu dari folder `mobile`:

```powershell
flutter pub get
flutter run                     # emulator: memakai http://10.0.2.2:5000 (alamat laptop dari dalam emulator)
```

Untuk HP sungguhan lewat kabel USB (cara paling ringan bila laptop tidak kuat menjalankan emulator), aktifkan
Opsi pengembang dan Debugging USB di HP, sambungkan kabel, lalu teruskan port 5000 HP ke laptop dengan `adb reverse`.
Flask tidak perlu `--host 0.0.0.0` dan tidak perlu satu WiFi:

```powershell
$adb = "$env:ANDROID_HOME\platform-tools\adb.exe"
& $adb devices
& $adb reverse tcp:5000 tcp:5000      # ulangi setiap kali kabel dicabut
flutter run --dart-define=API_BASE_URL=http://127.0.0.1:5000
```

Lewat WiFi, laptop dan HP harus berada di jaringan yang sama. Jalankan Flask dengan `--host 0.0.0.0`, lalu:

```powershell
ipconfig                        # lihat "IPv4 Address", misalnya 192.168.1.10
flutter run --dart-define=API_BASE_URL=http://192.168.1.10:5000
```

Bila HP tidak bisa terhubung, izinkan Python di Windows Defender Firewall untuk jaringan privat. Build debug boleh
memakai HTTP biasa; build rilis wajib HTTPS (alamat Railway nanti).

Masuk dengan akun demo perawat atau dokter dari `flask seed-demo` (lihat `backend/README.md`).

Catatan kode QR Eir: tautan di dalam kode QR memakai alamat yang dipakai aplikasi untuk memanggil server. Dari
emulator alamatnya `10.0.2.2`, dan lewat `adb reverse` alamatnya `127.0.0.1`. Keduanya hanya bisa dibuka dari
perangkat yang sama (emulator itu, atau peramban di HP yang tersambung kabel). Untuk mencoba Eir dari HP lain,
jalankan aplikasi dengan alamat IP laptop lewat WiFi.

Build pertama memakan waktu lama karena Gradle mengunduh dependensi Android sekali saja. Batas memori Gradle
diturunkan ke 3 GB di `android/gradle.properties` supaya tetap jalan di laptop dengan RAM terbatas.

## Pengujian dan lint

```powershell
flutter analyze
flutter test --coverage
dart run tool/cek_coverage.dart   # coverage tanpa kode hasil generate, minimal 80%
```

Tes widget memakai repository tiruan. Selain itu ada uji kontrak yang memanggil backend sungguhan dengan klien hasil
generate, untuk memastikan nama field, format tanggal, dan enum cocok. Uji ini tidak ikut `flutter test` biasa:

```powershell
flutter test test_backend --dart-define=API_UJI=http://127.0.0.1:5000 `
  --dart-define=PASSWORD_PERAWAT=isi-dari-env --dart-define=PASSWORD_DOKTER=isi-dari-env
```

## Build APK

```powershell
# Untuk uji coba di HP lewat WiFi laptop (HTTP diizinkan di build debug):
flutter build apk --debug --dart-define=API_BASE_URL=http://192.168.1.10:5000
# Untuk rilis setelah backend di-deploy (HTTPS):
flutter build apk --release --dart-define=API_BASE_URL=https://alamat-railway
```

Hasilnya ada di `build/app/outputs/flutter-apk/`. Build rilis masih ditandatangani dengan kunci debug; kunci rilis
disiapkan di tahap deployment.

## Klien API dari OpenAPI

Bila skema backend berubah, ekspor ulang spesifikasinya lalu bangkitkan ulang klien Dart:

```powershell
cd ..\backend; python -m flask --app run openapi -o ..\mobile\openapi.json -i 2
cd ..\mobile; dart run swagger_parser
dart run build_runner build --delete-conflicting-outputs
```

Hasilnya di `lib/api/generated/` dan tidak diubah manual. Endpoint admin, rekap, dan Eir pasien tidak ikut
dibangkitkan karena tidak dipakai aplikasi ini.

## Struktur

```
assets/         logo dan font Atkinson Hyperlegible Next beserta lisensinya
lib/
  tema.dart     warna, huruf, dan gaya komponen (panduan gaya tahap 6D)
  api/          klien HTTP (token, refresh), repository, error Problem Details, kode hasil generate
  state/        sesi login, papan prioritas dan peringatan, penyedia Riverpod
  halaman/      login, papan prioritas, pasien masuk, form observasi, pemindaian, hasil, riwayat, Eir, profil
  komponen/     penanda risk level, kotak pesan, blok, bilah tombol bawah, panel dan lembar peringatan
  util/         format waktu WIB, label, validasi isian
test/           unit dan widget test
test_backend/   uji kontrak dengan backend yang menyala
tool/           cek coverage
```
