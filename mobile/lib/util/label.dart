/// Label tampilan untuk nilai enum dari API.
library;

import '../api/generated/models/item_peringatan_jenis.dart';
import '../api/generated/models/jenis_alat.dart';
import '../api/generated/models/jenis_kelamin.dart';
import '../api/generated/models/jenis_triase.dart';
import '../api/generated/models/peran.dart';
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

/// L atau P seperti di kartu daftar tunggu.
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
  Peran.admin => 'Admin IGD',
  Peran.$unknown => '-',
};

String labelStatusValidasi(StatusValidasi status) => switch (status) {
  StatusValidasi.menunggu => 'Menunggu validasi',
  StatusValidasi.disetujui => 'Disetujui',
  StatusValidasi.menungguReviewDokter => 'Menunggu review dokter',
  StatusValidasi.dikoreksi => 'Dikoreksi dokter',
  StatusValidasi.$unknown => '-',
};

String labelSumberRekomendasi(SumberRekomendasi sumber) => switch (sumber) {
  SumberRekomendasi.model => 'Model AI (Random Forest)',
  SumberRekomendasi.aturan => 'Aturan cadangan',
  SumberRekomendasi.$unknown => '-',
};

String labelSumberTandaVital(SumberTandaVital sumber) => switch (sumber) {
  SumberTandaVital.manual => 'Diketik perawat',
  SumberTandaVital.pemindaian => 'Dibaca dari foto layar alat',
  SumberTandaVital.campuran => 'Sebagian dibaca dari foto',
  SumberTandaVital.$unknown => '-',
};

String labelJenisTriase(JenisTriase jenis) => jenis == JenisTriase.ulang ? 'Triase ulang' : 'Triase awal';

String labelStatusKunjungan(StatusKunjungan status) => switch (status) {
  StatusKunjungan.menunggu => 'Menunggu dokter',
  StatusKunjungan.ditangani => 'Sedang diperiksa',
  StatusKunjungan.selesai => 'Selesai',
  StatusKunjungan.$unknown => '-',
};

String labelKesadaran(TingkatKesadaran tingkat) => switch (tingkat) {
  TingkatKesadaran.a => 'A (sadar penuh)',
  TingkatKesadaran.v => 'V (respons suara)',
  TingkatKesadaran.p => 'P (respons nyeri)',
  TingkatKesadaran.u => 'U (tidak respons)',
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
  ItemPeringatanJenis.kritisBelumDivalidasi => 'Risk level kritis',
  ItemPeringatanJenis.levelNaik => 'Level naik',
  ItemPeringatanJenis.tandaBahayaEir => 'Tanda bahaya dari Eir',
  ItemPeringatanJenis.$unknown => 'Peringatan',
};

/// Nama kolom tanda vital, dipakai di form, hasil pemindaian, dan pesan error server.
const labelTandaVital = {
  'td_sistolik': 'TD sistolik',
  'td_diastolik': 'TD diastolik',
  'nadi': 'Nadi (x/mnt)',
  'saturasi': 'Saturasi O₂ (%)',
  'suhu': 'Suhu (°C)',
  'laju_napas': 'Laju napas (x/mnt)',
};

/// Urutan kolom tanda vital seperti di mockup Gambar 7.1.
const urutanTandaVital = ['td_sistolik', 'td_diastolik', 'nadi', 'saturasi', 'suhu', 'laju_napas'];
