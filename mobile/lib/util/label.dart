/// Label tampilan untuk nilai enum dari API.
library;

import '../api/generated/models/item_peringatan_jenis.dart';
import '../api/generated/models/jenis_alat.dart';
import '../api/generated/models/jenis_kelamin.dart';
import '../api/generated/models/jenis_triase.dart';
import '../api/generated/models/peran.dart';
import '../api/generated/models/registrasi_request_asal_ruangan.dart';
import '../api/generated/models/risk_level.dart';
import '../api/generated/models/status_kunjungan.dart';
import '../api/generated/models/status_validasi.dart';
import '../api/generated/models/sumber_rekomendasi.dart';
import '../api/generated/models/sumber_tanda_vital.dart';
import '../api/generated/models/tingkat_kesadaran.dart';

String labelLevel(RiskLevel level) => switch (level) {
  RiskLevel.kritis => 'Kritis',
  RiskLevel.tinggi => 'Tinggi',
  RiskLevel.sedang => 'Sedang',
  RiskLevel.rendah => 'Rendah',
  RiskLevel.$unknown => 'Tidak dikenal',
};

/// L atau P seperti di kartu papan prioritas.
String singkatanKelamin(JenisKelamin jenis) => switch (jenis) {
  JenisKelamin.lakiLaki => 'L',
  JenisKelamin.perempuan => 'P',
  JenisKelamin.$unknown => '-',
};

String labelKelamin(JenisKelamin jenis) => switch (jenis) {
  JenisKelamin.lakiLaki => 'Laki-laki',
  JenisKelamin.perempuan => 'Perempuan',
  JenisKelamin.$unknown => '-',
};

String labelPeran(Peran peran) => switch (peran) {
  Peran.perawat => 'Perawat',
  Peran.dokter => 'Dokter',
  Peran.admin => 'Admin ICU',
  Peran.$unknown => '-',
};

String labelStatusValidasi(StatusValidasi status) => switch (status) {
  StatusValidasi.menunggu => 'Menunggu persetujuan dokter',
  StatusValidasi.disetujui => 'Disetujui dokter',
  StatusValidasi.menungguReviewDokter => 'Review diajukan ke dokter',
  StatusValidasi.dikoreksi => 'Dikoreksi dokter',
  StatusValidasi.tercatat => 'Tercatat (level tidak naik)',
  StatusValidasi.$unknown => '-',
};

String labelSumberRekomendasi(SumberRekomendasi sumber) => switch (sumber) {
  SumberRekomendasi.model => 'NEWS2 dan model AI (Random Forest)',
  SumberRekomendasi.aturan => 'NEWS2 saja (model tidak tersedia)',
  SumberRekomendasi.$unknown => '-',
};

String labelSumberTandaVital(SumberTandaVital sumber) => switch (sumber) {
  SumberTandaVital.manual => 'Diketik perawat',
  SumberTandaVital.pemindaian => 'Dibaca dari foto layar alat',
  SumberTandaVital.campuran => 'Sebagian dibaca dari foto',
  SumberTandaVital.$unknown => '-',
};

String labelJenisTriase(JenisTriase jenis) => jenis == JenisTriase.ulang ? 'Observasi' : 'Penilaian awal';

String labelStatusKunjungan(StatusKunjungan status) => switch (status) {
  StatusKunjungan.menunggu => 'Dirawat',
  StatusKunjungan.ditangani => 'Sedang tindakan',
  StatusKunjungan.selesai => 'Keluar ICU',
  StatusKunjungan.$unknown => '-',
};

String labelKesadaran(TingkatKesadaran tingkat) => switch (tingkat) {
  TingkatKesadaran.a => 'A (sadar penuh)',
  TingkatKesadaran.v => 'V (respons suara)',
  TingkatKesadaran.p => 'P (respons nyeri)',
  TingkatKesadaran.u => 'U (tidak respons)',
  TingkatKesadaran.$unknown => '-',
};

/// Keterangan pendek di bawah huruf AVPU pada tombol pilihan kesadaran.
String singkatanKesadaran(TingkatKesadaran tingkat) => switch (tingkat) {
  TingkatKesadaran.a => 'sadar',
  TingkatKesadaran.v => 'suara',
  TingkatKesadaran.p => 'nyeri',
  TingkatKesadaran.u => 'tak respons',
  TingkatKesadaran.$unknown => '-',
};

String labelAlat(JenisAlat alat) => switch (alat) {
  JenisAlat.tensimeter => 'Tensimeter',
  JenisAlat.oksimeter => 'Oksimeter',
  JenisAlat.termometer => 'Termometer',
  JenisAlat.bedsideMonitor => 'Bedside monitor',
  JenisAlat.$unknown => '-',
};

String labelJenisPeringatan(ItemPeringatanJenis jenis) => switch (jenis) {
  ItemPeringatanJenis.menungguPersetujuan => 'Menunggu persetujuan dokter',
  ItemPeringatanJenis.observasiTerlambat => 'Observasi terlambat',
  ItemPeringatanJenis.informasiPentingEir => 'Informasi penting dari keluarga',
  ItemPeringatanJenis.$unknown => 'Peringatan',
};

/// Nama kolom tanda vital lengkap dengan satuan, dipakai di hasil pemindaian dan pesan error server.
const labelTandaVital = {
  'td_sistolik': 'TD sistolik',
  'td_diastolik': 'TD diastolik',
  'nadi': 'Nadi (x/mnt)',
  'saturasi': 'Saturasi O₂ (%)',
  'suhu': 'Suhu (°C)',
  'laju_napas': 'Laju napas (x/mnt)',
};

/// Nama pendek dan satuan untuk kotak isian di Form Observasi; satuannya ditulis di dalam kotak.
const labelPendekTandaVital = {
  'td_sistolik': 'Sistolik',
  'td_diastolik': 'Diastolik',
  'nadi': 'Nadi',
  'saturasi': 'SpO₂',
  'suhu': 'Suhu',
  'laju_napas': 'Laju napas',
};

const satuanTandaVital = {
  'td_sistolik': 'mmHg',
  'td_diastolik': 'mmHg',
  'nadi': 'x/mnt',
  'saturasi': '%',
  'suhu': '°C',
  'laju_napas': 'x/mnt',
};

/// Urutan kolom tanda vital seperti di mockup Gambar 7.1.
const urutanTandaVital = ['td_sistolik', 'td_diastolik', 'nadi', 'saturasi', 'suhu', 'laju_napas'];

/// Hasil laboratorium opsional di Form Observasi: label, satuan, dan jumlah desimal yang diterima server.
const kolomLab = <String, (String, String, int)>{
  'laktat': ('Laktat', 'mmol/L', 1),
  'kreatinin': ('Kreatinin', 'mg/dL', 2),
  'trombosit': ('Trombosit', 'rb/µL', 0),
  'leukosit': ('Leukosit', 'rb/µL', 1),
  'bilirubin': ('Bilirubin', 'mg/dL', 1),
};

/// Pilihan asal ruangan saat pasien masuk ICU, sama dengan nilai yang diterima backend.
String labelAsalRuangan(RegistrasiRequestAsalRuangan asal) => asal.json ?? '-';

/// Persen peluang perburukan, misalnya 0.7412 menjadi "74%".
String persenPeluang(num peluang) => '${(peluang * 100).round()}%';
