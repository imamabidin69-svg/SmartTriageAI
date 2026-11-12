# Catatan Perubahan Lingkup: dari Triase IGD ke Prioritas Pasien ICU

Dokumen ini menjelaskan kenapa SmartTriage AI sekarang dipakai untuk menentukan urutan penanganan pasien ICU,
padahal SKPL yang sudah ditandatangani menulis triase IGD. Isinya alasan perubahan, pemetaan kebutuhan
fungsional SKPL ke versi ICU, apa saja yang berubah di sistem, dan batasan yang masih ada.

## 1. Latar belakang

Saat presentasi progres, dosen memberi masukan berikut:

> Daripada penanganan yang berada di depan, mending yang berada di belakang, jadi di ICU, pembacaan mana pasien
> yang harus di operasi/ditangani terlebih dahulu, tetapi tetap dengan persetujuan dokter. Menambah metode,
> membaca alat, dan klasifikasi mana yang harus ditangani terlebih dahulu.

Dari masukan itu ada empat hal yang kami ambil:

1. Lokasi pemakaian pindah dari IGD (pintu depan) ke ICU (pasien yang sudah dirawat).
2. Keluaran sistem adalah urutan pasien yang harus ditangani lebih dulu, bukan rekomendasi tindakan.
3. Keputusan akhir tetap di dokter.
4. Ada metode tambahan, pembacaan alat, dan klasifikasi prioritas.

Kami memilih mengganti fokus IGD dengan ICU, bukan menambah modul baru di samping IGD, supaya jumlah fitur tidak
membengkak dan SKPL tidak perlu ditulis ulang.

## 2. Kenapa perubahan ini masih sejalan dengan SKPL

Masalah yang diselesaikan SKPL tetap sama: **menentukan pasien mana yang perlu ditangani lebih dulu dengan
bantuan AI yang bisa dijelaskan, lalu divalidasi tenaga medis**. Yang berubah adalah tempat dan data
masukannya.

- **Aktor tetap sama.** Perawat mencatat data pasien, dokter memvalidasi, admin mengatur sistem, dan keluarga
  memakai Eir. Di SKPL, Eir sudah bisa dipakai keluarga pendamping.
- **Alur utama tetap sama.** Data pasien masuk, sistem memberi level Kritis/Tinggi/Sedang/Rendah beserta
  penjelasannya, tenaga medis memvalidasi, dan pasien dipantau ulang secara berkala. Di IGD siklus ini disebut
  triase dan triase ulang, di ICU disebut penilaian awal dan observasi.
- **Struktur data hampir tidak berubah.** Delapan tabel PDM SKPL tetap dipakai. Tabel `kunjungan` dibaca sebagai
  satu masa rawat di ICU dan tabel `triase` sebagai satu observasi. Perubahannya hanya penambahan kolom, bukan
  tabel baru.
- **SKPL sudah menyiapkan sebagian kebutuhan ICU.** Jenis alat `bedside_monitor`, triase ulang, peringatan level
  naik, dan validasi dokter sudah ada sejak awal.
- **Data latih lebih jelas asal-usulnya.** Model IGD sebelumnya memakai data KTAS dari Kaggle yang lisensinya
  belum jelas. Model ICU memakai data PhysioNet 2019 dengan lisensi CC BY 4.0 dan 40 ribu pasien ICU.
- **Metode tambahan yang diminta dosen terpenuhi.** NEWS2 ditambahkan sebagai metode kedua di samping Random
  Forest, sehingga penilaian tetap jalan walau model AI tidak tersedia.

Jadi perubahan ini kami anggap penyesuaian konteks pemakaian (IGD menjadi ICU), bukan perubahan kebutuhan.

## 3. Pemetaan kebutuhan fungsional

| SKPL | Di IGD (sebelumnya) | Di ICU (sekarang) |
| --- | --- | --- |
| FR-01 Autentikasi dan akun | Admin, perawat, dokter | Sama |
| FR-02 Registrasi pasien | Registrasi singkat, kunjungan menunggu | Pasien masuk ICU: nomor bed (satu bed satu pasien aktif), asal ruangan, diagnosis masuk |
| FR-03 Input triase | Keluhan, kategori keluhan, skala nyeri, AVPU, tanda vital | Observasi: tanda vital, AVPU, oksigen tambahan, lima hasil lab opsional (laktat, kreatinin, trombosit, leukosit, bilirubin), ventilator, vasopresor, catatan |
| FR-04 Pemindaian layar alat | Tensimeter, oksimeter, termometer, bedside monitor | Sama; tombol di form diberi nama "Pindai monitor" |
| FR-05 Rekomendasi dan penjelasan | Random Forest 4 kelas dari data KTAS + SHAP, aturan cadangan | Skor NEWS2 + Random Forest peluang memburuk 6 jam dari data PhysioNet + SHAP; level akhir yang lebih tinggi dari keduanya; NEWS2 menjadi cadangan bila model tidak ada |
| FR-06 Validasi | Perawat menyetujui hasil non-kritis, dokter semua level | Hanya dokter yang menyetujui atau mengoreksi; persetujuan diminta pada penilaian awal dan **setiap kali level naik**; observasi yang levelnya sama atau turun langsung tercatat; perawat bisa mengajukan review |
| FR-07 Daftar tunggu, peringatan, konfigurasi | Daftar tunggu urut level, batas waktu tunggu, triase ulang | Papan prioritas ICU (urutan penanganan), interval observasi per level, peringatan menunggu persetujuan, observasi terlambat, dan informasi penting dari Eir; ambang NEWS2 bisa diatur admin |
| FR-08 Eir | Anamnesis keluhan pasien zona hijau, tanda bahaya menghentikan sesi | Menggali riwayat pasien dari keluarga: kronologi, riwayat penyakit, obat rutin, alergi, riwayat operasi, kebiasaan; informasi penting (alergi obat, pengencer darah, insulin, kehamilan, alat implan, masalah pembiusan, penyakit menular, keinginan pasien) ditandai untuk perawat tanpa menghentikan percakapan |
| FR-09 Riwayat dan rekap | Riwayat triase, rekap per level | Riwayat observasi (dengan bed, NEWS2, peluang), rekap per level |

Kebutuhan nonfungsional (keamanan, audit, waktu respons, fallback saat model gagal, coverage tes) tetap sama.

## 4. Cara sistem menentukan urutan penanganan

1. **NEWS2** (Royal College of Physicians, 2017) dihitung dari laju napas, saturasi, oksigen tambahan, tekanan
   darah sistolik, nadi, kesadaran, dan suhu. Skor 0 sampai 20. Ambang bawaan: 7 Kritis, 5 Tinggi, 3 Sedang,
   dan satu parameter bernilai 3 minimal Sedang. Ambang bisa diubah admin.
2. **Model Random Forest** memperkirakan peluang pasien memburuk dalam 6 jam. Peluang diubah ke level memakai
   ambang yang dipilih dari data latih. Tiga faktor SHAP terbesar ditampilkan sebagai penjelasan.
3. **Level akhir** adalah yang lebih tinggi dari NEWS2 dan model, supaya model tidak pernah menurunkan level
   yang sudah ditunjukkan NEWS2.
4. **Papan prioritas** mengurutkan pasien: Kritis, belum dinilai, Tinggi, Sedang, Rendah. Di level yang sama,
   pasien yang menunggu persetujuan dokter dan yang observasinya terlambat didahulukan, lalu peluang memburuk
   dan skor NEWS2 tertinggi. Pasien yang sedang tindakan atau operasi ditaruh paling bawah.
5. **Interval observasi** bawaan: Kritis 15 menit, Tinggi 30, Sedang 60, Rendah 120. Bila terlewat, pasien
   ditandai "observasi terlambat".
6. **Persetujuan dokter** diminta saat penilaian awal dan setiap kali level naik dibanding level final terakhir.

Status pasien di ICU: dirawat (`menunggu`), sedang tindakan atau operasi (`ditangani`, bisa kembali ke dirawat),
dan keluar ICU (`selesai`).

## 5. Ringkasan perubahan teknis

- **Basis data**: migrasi Alembic `0002_prioritas_icu` (bisa diturunkan kembali ke 0001). Kolom keluhan IGD
  di tabel `triase` diganti kolom ICU, status validasi `tercatat` ditambahkan, tabel `kunjungan` mendapat
  `nomor_bed`, `asal_ruangan`, `diagnosis_masuk`, dan tabel `konfigurasi` mendapat `batas_tunggu_kritis`.
- **AI**: `app/ai/news2.py` baru, `app/ai/klasifikasi.py` ditulis ulang, model baru
  `rf-icu-physionet2019-v1`, skrip `ai_training/perburukan.py`, dan laporan `ai_training/laporan_model_icu.json`.
- **Eir**: enam panduan topik riwayat menggantikan 18 panduan kategori keluhan, detektor informasi penting
  menggantikan detektor tanda bahaya, dan ringkasan berisi kronologi, riwayat penyakit, obat rutin, alergi, serta
  informasi lain.
- **Aplikasi Android**: Papan Prioritas ICU, Pasien Masuk ICU, Form Observasi, Hasil Penilaian dengan NEWS2 dan
  peluang memburuk, tombol status tindakan dan keluar ICU untuk dokter.
- **Web admin**: pengaturan ambang NEWS2 dan interval observasi, label rekap dan log audit, halaman Eir untuk
  keluarga.
- **Data simulasi**: `flask seed-demo --dengan-pasien` membuat 8 bed ICU dengan pasien fiktif.

Nama tabel, nama endpoint (`/kunjungan/{id}/triase`, `/daftar-tunggu`), dan nama kelas di kode tetap mengikuti
SKPL supaya dokumen desain dan kode masih bisa dicocokkan.

## 6. Batasan dan hal yang perlu dikonfirmasi

- Label model memakai `SepsisLabel` sebagai pendekatan "akan memburuk". Sepsis adalah salah satu penyebab
  perburukan tersering di ICU, tetapi bukan satu-satunya. AUROC model 0,736 pada pasien uji.
- Data PhysioNet berasal dari pasien dewasa di Amerika Serikat. Untuk pasien di bawah 18 tahun aplikasi memberi
  peringatan.
- Jumlah bed (8) adalah angka simulasi karena belum ada angka dari dosen.
- Angka dari foto bedside monitor belum dipetakan otomatis ke kolom karena tata letak monitor berbeda antar
  merek; perawat mengisinya manual. Model YOLO pembaca digit (`yolo_digit.onnx`) dilatih dari enam dataset
  Roboflow Universe berlisensi CC BY 4.0. Pada 19 foto tensimeter uji dengan ambang keyakinan 0,6, 48 dari 57
  kolom terisi dan semuanya benar (rincian di `backend/ai_training/laporan_model_yolo.json`). Dataset
  Cloudphysician (2.000 foto monitor ICU) dan alx-xlaxal sudah tersedia untuk tahap berikutnya, yaitu memotong
  layar monitor dan menandai area tanda vital sebelum digit dibaca.
- Pola informasi penting Eir dan panduan pertanyaan masih draf dan perlu ditinjau tenaga medis.
- Semua data pasien di sistem adalah data simulasi.

## 7. Sumber

- Reyna MA, dkk. Early Prediction of Sepsis From Clinical Data: The PhysioNet/Computing in Cardiology Challenge
  2019. Critical Care Medicine, 2020. Data: https://physionet.org/content/challenge-2019/1.0.0/ (CC BY 4.0).
- Royal College of Physicians. National Early Warning Score (NEWS) 2: Standardising the assessment of
  acute-illness severity in the NHS. London: RCP, 2017.
- Lundberg SM, Lee SI. A Unified Approach to Interpreting Model Predictions. NeurIPS, 2017 (SHAP).
