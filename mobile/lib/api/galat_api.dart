import 'package:dio/dio.dart';

/// Error dari API dalam format Problem Details (RFC 9457), atau gangguan jaringan bila server tidak terjangkau.
///
/// Pesan per field dipetakan ke [pesanField] supaya form bisa menyorot kolom yang salah tanpa menghapus isian
/// lain, sama seperti aplikasi web (Desain bagian 8).
class GalatApi implements Exception {
  const GalatApi({
    required this.status,
    required this.tipe,
    required this.judul,
    this.detail,
    this.pesanField = const {},
    this.ekstra = const {},
  });

  static const tipeJaringan = 'jaringan';
  static const tipeTokenKedaluwarsa = 'urn:smarttriage:problem:token-kedaluwarsa';
  static const tipeTidakTerautentikasi = 'urn:smarttriage:problem:tidak-terautentikasi';
  static const tipeKredensialSalah = 'urn:smarttriage:problem:kredensial-salah';
  static const tipeSesiBerakhir = 'urn:smarttriage:problem:sesi-berakhir';
  static const tipeAksesDitolak = 'urn:smarttriage:problem:akses-ditolak';
  static const tipeKonflik = 'urn:smarttriage:problem:konflik';

  /// Kode HTTP; 0 bila request tidak sampai ke server.
  final int status;
  final String tipe;
  final String judul;
  final String? detail;
  final Map<String, String> pesanField;

  /// Field tambahan Problem Details, misalnya id_kunjungan_aktif pada konflik registrasi.
  final Map<String, Object?> ekstra;

  bool get jaringan => status == 0;

  /// Pesan untuk ditampilkan: detail bila ada, selain itu judul.
  String get pesan => detail ?? judul;

  /// Pesan untuk satu field. Field bersarang ditulis dengan titik, misalnya tanda_vital.suhu.
  String? field(String nama) => pesanField[nama];

  factory GalatApi.dari(Object galat) {
    if (galat is GalatApi) return galat;
    if (galat is DioException) return GalatApi._dariDio(galat);
    return GalatApi(status: -1, tipe: 'tidak-dikenal', judul: 'Terjadi kesalahan. Coba lagi.', detail: '$galat');
  }

  factory GalatApi._dariDio(DioException galat) {
    final respons = galat.response;
    if (respons == null) {
      final waktuHabis =
          galat.type == DioExceptionType.connectionTimeout ||
          galat.type == DioExceptionType.receiveTimeout ||
          galat.type == DioExceptionType.sendTimeout;
      return GalatApi(
        status: 0,
        tipe: tipeJaringan,
        judul: waktuHabis
            ? 'Server terlalu lama menjawab. Periksa jaringan lalu coba lagi.'
            : 'Tidak dapat terhubung ke server. Periksa jaringan lalu coba lagi.',
      );
    }
    final isi = respons.data;
    if (isi is Map && isi['title'] is String) {
      final field = <String, String>{};
      final daftar = isi['errors'];
      if (daftar is List) {
        for (final item in daftar) {
          if (item is Map && item['field'] is String && item['pesan'] is String) {
            // Pesan pertama per field yang dipakai, seperti di aplikasi web.
            field.putIfAbsent(item['field'] as String, () => item['pesan'] as String);
          }
        }
      }
      const bawaan = {'type', 'title', 'status', 'detail', 'instance', 'errors'};
      return GalatApi(
        status: respons.statusCode ?? 0,
        tipe: isi['type'] is String ? isi['type'] as String : 'about:blank',
        judul: isi['title'] as String,
        detail: isi['detail'] is String ? isi['detail'] as String : null,
        pesanField: field,
        ekstra: {
          for (final MapEntry(:key, :value) in isi.entries)
            if (key is String && !bawaan.contains(key)) key: value,
        },
      );
    }
    return GalatApi(
      status: respons.statusCode ?? 0,
      tipe: 'about:blank',
      judul: 'Server menjawab dengan kode ${respons.statusCode}. Coba lagi.',
    );
  }

  @override
  String toString() => 'GalatApi($status, $tipe, $pesan)';
}
