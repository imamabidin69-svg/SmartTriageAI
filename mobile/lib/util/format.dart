/// Format waktu dan angka berbahasa Indonesia. Waktu dari server dalam UTC dan selalu ditampilkan dalam WIB,
/// sama seperti aplikasi web, supaya tidak bergantung pada zona waktu perangkat.
library;

const _bulan = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'];

DateTime keWib(DateTime waktu) => waktu.toUtc().add(const Duration(hours: 7));

String _dua(int angka) => angka.toString().padLeft(2, '0');

/// "08.42", seperti di mockup daftar tunggu.
String jamWib(DateTime waktu) {
  final wib = keWib(waktu);
  return '${_dua(wib.hour)}.${_dua(wib.minute)}';
}

/// "17 Okt 2026".
String tanggalWib(DateTime waktu) {
  final wib = keWib(waktu);
  return '${wib.day} ${_bulan[wib.month - 1]} ${wib.year}';
}

/// "17 Okt 2026 08.42".
String tanggalJamWib(DateTime waktu) => '${tanggalWib(waktu)} ${jamWib(waktu)}';

/// Tanggal lahir dari server berupa tanggal tanpa jam, jadi tidak digeser ke WIB.
String tanggalSaja(DateTime tanggal) => '${tanggal.day} ${_bulan[tanggal.month - 1]} ${tanggal.year}';

/// Tanggal untuk dikirim ke server (YYYY-MM-DD).
String tanggalIso(DateTime tanggal) => '${tanggal.year}-${_dua(tanggal.month)}-${_dua(tanggal.day)}';

/// Angka desimal dengan koma, misalnya 37,2. Bilangan bulat ditulis tanpa koma.
String angka(num nilai) {
  if (nilai == nilai.roundToDouble()) return nilai.round().toString();
  return nilai.toStringAsFixed(1).replaceAll('.', ',');
}

/// Mengubah isian angka pengguna (boleh memakai koma) menjadi num, atau null bila bukan angka.
num? bacaAngka(String teks) {
  final rapi = teks.trim().replaceAll(',', '.');
  if (rapi.isEmpty) return null;
  return num.tryParse(rapi);
}

/// "12 mnt", atau "1 jam 5 mnt" untuk tunggu yang lama.
String durasiMenit(int menit) {
  if (menit < 60) return '$menit mnt';
  final sisa = menit % 60;
  return sisa == 0 ? '${menit ~/ 60} jam' : '${menit ~/ 60} jam $sisa mnt';
}
