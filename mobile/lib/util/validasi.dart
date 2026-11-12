/// Pemeriksaan isian di perangkat, sama dengan batas di skema Pydantic backend, supaya perawat langsung tahu
/// kolom yang salah sebelum data dikirim. Server tetap memeriksa ulang.
library;

import 'format.dart';

/// Batas nilai yang mungkin dicatat per kolom tanda vital (sama dengan CHECK di basis data).
const batasTandaVital = <String, (num, num)>{
  'td_sistolik': (0, 320),
  'td_diastolik': (0, 200),
  'nadi': (0, 300),
  'laju_napas': (0, 80),
  'suhu': (20, 45),
  'saturasi': (0, 100),
};

const kolomDesimal = {'suhu', 'saturasi'};

String? periksaTandaVital(String kolom, String teks) {
  final nilai = bacaAngka(teks);
  if (teks.trim().isEmpty) return 'Wajib diisi.';
  if (nilai == null) return 'Isi dengan angka.';
  if (!kolomDesimal.contains(kolom) && nilai != nilai.roundToDouble()) return 'Isi dengan bilangan bulat.';
  final (bawah, atas) = batasTandaVital[kolom]!;
  if (nilai < bawah || nilai > atas) return 'Harus antara ${angka(bawah)} dan ${angka(atas)}.';
  return null;
}

/// Batas hasil lab (sama dengan skema HasilLab di backend). Lab boleh kosong.
const batasLab = <String, (num, num)>{
  'laktat': (0, 30),
  'kreatinin': (0, 25),
  'trombosit': (0, 2000),
  'leukosit': (0, 300),
  'bilirubin': (0, 60),
};

String? periksaLab(String kolom, String teks) {
  if (teks.trim().isEmpty) return null;
  final nilai = bacaAngka(teks);
  if (nilai == null) return 'Isi dengan angka.';
  if (kolom == 'trombosit' && nilai != nilai.roundToDouble()) return 'Isi dengan bilangan bulat.';
  final (bawah, atas) = batasLab[kolom]!;
  if (nilai < bawah || nilai > atas) return 'Harus antara ${angka(bawah)} dan ${angka(atas)}.';
  return null;
}

/// Nomor bed wajib: huruf, angka, spasi, dan tanda hubung, maksimal 10 karakter (sama dengan backend).
String? periksaNomorBed(String teks) {
  final isi = teks.trim();
  if (isi.isEmpty) return 'Nomor bed wajib diisi.';
  if (isi.length > 10) return 'Nomor bed maksimal 10 karakter.';
  if (!RegExp(r'^[A-Za-z0-9][A-Za-z0-9 -]*$').hasMatch(isi)) {
    return 'Hanya huruf, angka, spasi, dan tanda hubung.';
  }
  return null;
}

String? periksaPanjang(String teks, {required int min, required int maks, required String nama}) {
  final panjang = teks.trim().length;
  if (panjang == 0) return '$nama wajib diisi.';
  if (panjang < min) return '$nama minimal $min karakter.';
  if (panjang > maks) return '$nama maksimal $maks karakter.';
  return null;
}

/// NIK opsional, tetapi bila diisi harus 16 digit.
String? periksaNik(String teks) {
  final isi = teks.trim();
  if (isi.isEmpty) return null;
  return RegExp(r'^\d{16}$').hasMatch(isi) ? null : 'NIK harus 16 digit angka.';
}

/// Nomor telepon opsional, aturan sama dengan backend: angka, spasi, tanda hubung, dan + di depan.
String? periksaTelepon(String teks) {
  final isi = teks.trim();
  if (isi.isEmpty) return null;
  if (isi.length > 20 || !RegExp(r'^\+?[0-9][0-9 -]{5,19}$').hasMatch(isi)) {
    return 'Nomor telepon hanya boleh berisi angka, spasi, tanda hubung, dan tanda + di depan.';
  }
  return null;
}

String? periksaUsia(String teks) {
  final nilai = int.tryParse(teks.trim());
  if (teks.trim().isEmpty) return 'Isi tanggal lahir atau perkiraan usia.';
  if (nilai == null || nilai < 0 || nilai > 150) return 'Usia 0 sampai 150 tahun.';
  return null;
}
