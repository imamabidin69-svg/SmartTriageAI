// Menghitung coverage baris dari coverage/lcov.info tanpa kode hasil generate, lalu gagal bila di bawah batas.
// Jalankan setelah `flutter test --coverage`:  dart run tool/cek_coverage.dart
import 'dart:io';

const batasPersen = 80.0;
const dikecualikan = ['lib/api/generated/'];

void main(List<String> argumen) {
  final berkas = File(argumen.isEmpty ? 'coverage/lcov.info' : argumen.first);
  if (!berkas.existsSync()) {
    stderr.writeln('${berkas.path} tidak ada. Jalankan dulu: flutter test --coverage');
    exit(2);
  }
  final hasil = <String, (int, int)>{};
  String? nama;
  var ditemukan = 0;
  var tercakup = 0;
  for (final baris in berkas.readAsLinesSync()) {
    if (baris.startsWith('SF:')) {
      nama = baris.substring(3).replaceAll(r'\', '/');
      ditemukan = 0;
      tercakup = 0;
    } else if (baris.startsWith('DA:')) {
      ditemukan++;
      if (!baris.endsWith(',0')) tercakup++;
    } else if (baris == 'end_of_record' && nama != null) {
      if (!dikecualikan.any(nama.contains)) hasil[nama] = (tercakup, ditemukan);
      nama = null;
    }
  }
  var total = 0;
  var kena = 0;
  for (final MapEntry(key: nama, value: (cakup, semua))
      in hasil.entries.toList()..sort((a, b) => a.key.compareTo(b.key))) {
    total += semua;
    kena += cakup;
    final persen = semua == 0 ? 100.0 : cakup * 100 / semua;
    stdout.writeln('${persen.toStringAsFixed(1).padLeft(6)}%  $cakup/$semua  $nama');
  }
  final persen = total == 0 ? 0.0 : kena * 100 / total;
  stdout.writeln('Total ${persen.toStringAsFixed(2)}% ($kena/$total baris, tanpa ${dikecualikan.join(', ')})');
  if (persen < batasPersen) {
    stderr.writeln('Coverage di bawah $batasPersen%.');
    exit(1);
  }
}
