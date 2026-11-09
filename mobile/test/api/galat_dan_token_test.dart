import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smarttriage_mobile/api/galat_api.dart';
import 'package:smarttriage_mobile/api/penyimpanan_token.dart';

DioException _galatDengan(int status, Object? isi) {
  final opsi = RequestOptions(path: '/x');
  return DioException.badResponse(
    statusCode: status,
    requestOptions: opsi,
    response: Response<Object?>(requestOptions: opsi, statusCode: status, data: isi),
  );
}

void main() {
  group('GalatApi', () {
    test('membaca Problem Details beserta pesan per field dan field tambahan', () {
      final galat = GalatApi.dari(
        _galatDengan(409, {
          'type': GalatApi.tipeKonflik,
          'title': 'Konflik',
          'status': 409,
          'detail': 'Pasien ini masih punya kunjungan aktif.',
          'instance': '/api/v1/kunjungan',
          'errors': [
            {'field': 'nik', 'pesan': 'NIK sudah terdaftar.'},
            {'field': 'nik', 'pesan': 'Pesan kedua diabaikan.'},
            {'field': 1, 'pesan': 'bukan field'},
            'bukan objek',
          ],
          'id_kunjungan_aktif': 'k1',
        }),
      );
      expect(galat.status, 409);
      expect(galat.tipe, GalatApi.tipeKonflik);
      expect(galat.pesan, 'Pasien ini masih punya kunjungan aktif.');
      expect(galat.pesanField, {'nik': 'NIK sudah terdaftar.'});
      expect(galat.ekstra, {'id_kunjungan_aktif': 'k1'});
      expect(galat.jaringan, isFalse);
      expect(galat.toString(), contains('409'));
    });

    test('tanpa detail dan tanpa type memakai judul', () {
      final galat = GalatApi.dari(_galatDengan(500, {'title': 'Kesalahan server', 'status': 500}));
      expect(galat.pesan, 'Kesalahan server');
      expect(galat.tipe, 'about:blank');
    });

    test('jawaban yang bukan Problem Details', () {
      final galat = GalatApi.dari(_galatDengan(502, '<html>Bad gateway</html>'));
      expect(galat.pesan, 'Server menjawab dengan kode 502. Coba lagi.');
    });

    test('server tidak terjangkau dan waktu habis', () {
      final opsi = RequestOptions(path: '/x');
      final putus = GalatApi.dari(DioException.connectionError(requestOptions: opsi, reason: 'x'));
      expect(putus.jaringan, isTrue);
      expect(putus.pesan, startsWith('Tidak dapat terhubung'));
      final lama = GalatApi.dari(
        DioException.receiveTimeout(timeout: const Duration(seconds: 1), requestOptions: opsi),
      );
      expect(lama.pesan, startsWith('Server terlalu lama menjawab'));
    });

    test('error lain dibungkus dan GalatApi dikembalikan apa adanya', () {
      const asli = GalatApi(status: 401, tipe: 't', judul: 'j');
      expect(identical(GalatApi.dari(asli), asli), isTrue);
      expect(GalatApi.dari(StateError('x')).status, -1);
    });
  });

  group('Penyimpanan token', () {
    TestWidgetsFlutterBinding.ensureInitialized();

    test('flutter_secure_storage menyimpan, mengganti, dan menghapus token', () async {
      FlutterSecureStorage.setMockInitialValues({});
      final penyimpanan = PenyimpananTokenAman();
      expect(await penyimpanan.baca(), isNull);
      await penyimpanan.simpan(const TokenSesi(akses: 'a1', refresh: 'r1'));
      await penyimpanan.gantiAkses('a2');
      final token = await penyimpanan.baca();
      expect((token!.akses, token.refresh), ('a2', 'r1'));
      await penyimpanan.hapus();
      expect(await penyimpanan.baca(), isNull);
    });

    test('penyimpanan memori tidak mengganti akses bila belum ada token', () async {
      final penyimpanan = PenyimpananTokenMemori();
      await penyimpanan.gantiAkses('a');
      expect(await penyimpanan.baca(), isNull);
    });
  });
}
