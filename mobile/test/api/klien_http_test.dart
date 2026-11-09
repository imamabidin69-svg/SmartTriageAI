import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smarttriage_mobile/api/galat_api.dart';
import 'package:smarttriage_mobile/api/klien_http.dart';
import 'package:smarttriage_mobile/api/penyimpanan_token.dart';

import '../bantuan/http.dart';

void main() {
  late PenyimpananTokenMemori token;
  late int sesiBerakhir;

  setUp(() {
    token = PenyimpananTokenMemori(const TokenSesi(akses: 'akses-lama', refresh: 'refresh-1'));
    sesiBerakhir = 0;
  });

  KlienHttp buat(AdapterPalsu adapter) =>
      KlienHttp(alamat: 'http://server', token: token, saatSesiBerakhir: () => sesiBerakhir++, adapter: adapter);

  String? bearer(RequestOptions opsi) => opsi.headers['Authorization'] as String?;

  test('setiap request membawa access token dari penyimpanan', () async {
    final adapter = AdapterPalsu((_) async => jawabanJson(200, {'ok': true}));
    final respons = await buat(adapter).dio.get<Map<String, dynamic>>('/api/v1/daftar-tunggu');
    expect(respons.data, {'ok': true});
    expect(bearer(adapter.permintaan.single), 'Bearer akses-lama');
    expect(adapter.permintaan.single.uri.toString(), 'http://server/api/v1/daftar-tunggu');
  });

  test('tanpa token tersimpan tidak ada header Authorization', () async {
    await token.hapus();
    final adapter = AdapterPalsu((_) async => jawabanJson(200, {}));
    await buat(adapter).dio.get<void>('/api/v1/health');
    expect(bearer(adapter.permintaan.single), isNull);
  });

  test('access token kedaluwarsa diperbarui lalu request diulang sekali', () async {
    final adapter = AdapterPalsu((opsi) async {
      if (opsi.path == '/api/v1/auth/refresh') {
        expect(bearer(opsi), 'Bearer refresh-1');
        return jawabanJson(200, {'access_token': 'akses-baru', 'token_type': 'Bearer'});
      }
      if (bearer(opsi) == 'Bearer akses-lama') {
        return jawabanJson(401, problem(401, GalatApi.tipeTokenKedaluwarsa));
      }
      return jawabanJson(200, {'items': []});
    });
    final respons = await buat(adapter).dio.get<Map<String, dynamic>>('/api/v1/daftar-tunggu');
    expect(respons.data, {'items': []});
    expect(adapter.permintaan.map((o) => o.path), [
      '/api/v1/daftar-tunggu',
      '/api/v1/auth/refresh',
      '/api/v1/daftar-tunggu',
    ]);
    expect(bearer(adapter.permintaan.last), 'Bearer akses-baru');
    expect((await token.baca())!.akses, 'akses-baru');
    expect((await token.baca())!.refresh, 'refresh-1');
  });

  test('beberapa request yang gagal bersamaan cukup memakai satu refresh', () async {
    final refreshSelesai = Completer<void>();
    final adapter = AdapterPalsu((opsi) async {
      if (opsi.path == '/api/v1/auth/refresh') {
        await refreshSelesai.future;
        return jawabanJson(200, {'access_token': 'akses-baru'});
      }
      if (bearer(opsi) == 'Bearer akses-lama') return jawabanJson(401, problem(401, GalatApi.tipeTidakTerautentikasi));
      return jawabanJson(200, {'jalur': opsi.path});
    });
    final klien = buat(adapter);
    final hasil = Future.wait([
      klien.dio.get<Map<String, dynamic>>('/api/v1/daftar-tunggu'),
      klien.dio.get<Map<String, dynamic>>('/api/v1/peringatan'),
    ]);
    await Future<void>.delayed(Duration.zero);
    refreshSelesai.complete();
    final respons = await hasil;
    expect(respons.map((r) => r.data!['jalur']), ['/api/v1/daftar-tunggu', '/api/v1/peringatan']);
    expect(adapter.permintaan.where((o) => o.path == '/api/v1/auth/refresh'), hasLength(1));
  });

  test('refresh token ditolak: token dihapus dan sesi berakhir', () async {
    final adapter = AdapterPalsu((opsi) async {
      if (opsi.path == '/api/v1/auth/refresh') return jawabanJson(401, problem(401, GalatApi.tipeTokenKedaluwarsa));
      return jawabanJson(401, problem(401, GalatApi.tipeTokenKedaluwarsa));
    });
    await expectLater(
      buat(adapter).dio.get<void>('/api/v1/daftar-tunggu'),
      throwsA(isA<DioException>().having((e) => e.response?.statusCode, 'status', 401)),
    );
    expect(await token.baca(), isNull);
    expect(sesiBerakhir, 1);
  });

  test('refresh gagal karena jaringan tidak menghapus sesi', () async {
    final adapter = AdapterPalsu((opsi) async {
      if (opsi.path == '/api/v1/auth/refresh') {
        throw DioException.connectionError(requestOptions: opsi, reason: 'putus');
      }
      return jawabanJson(401, problem(401, GalatApi.tipeTokenKedaluwarsa));
    });
    await expectLater(buat(adapter).dio.get<void>('/api/v1/peringatan'), throwsA(isA<DioException>()));
    expect(await token.baca(), isNotNull);
    expect(sesiBerakhir, 0);
  });

  test('jawaban refresh tanpa access token dianggap gagal', () async {
    final adapter = AdapterPalsu((opsi) async {
      if (opsi.path == '/api/v1/auth/refresh') return jawabanJson(200, {'pengguna': {}});
      return jawabanJson(401, problem(401, GalatApi.tipeTokenKedaluwarsa));
    });
    await expectLater(buat(adapter).dio.get<void>('/api/v1/peringatan'), throwsA(isA<DioException>()));
    expect(adapter.permintaan, hasLength(2));
  });

  test('akun dinonaktifkan di tengah sesi: token dihapus dan kembali ke login', () async {
    final adapter = AdapterPalsu((_) async => jawabanJson(401, problem(401, GalatApi.tipeSesiBerakhir)));
    await expectLater(buat(adapter).dio.get<void>('/api/v1/daftar-tunggu'), throwsA(isA<DioException>()));
    expect(adapter.permintaan, hasLength(1));
    expect(await token.baca(), isNull);
    expect(sesiBerakhir, 1);
  });

  test('401 lain, misalnya password salah, tidak memicu refresh', () async {
    final adapter = AdapterPalsu((_) async => jawabanJson(401, problem(401, GalatApi.tipeKredensialSalah)));
    await expectLater(buat(adapter).dio.post<void>('/api/v1/auth/login'), throwsA(isA<DioException>()));
    expect(adapter.permintaan, hasLength(1));
  });

  test('token dihapus di tengah jalan: error diteruskan tanpa refresh', () async {
    late KlienHttp klien;
    final adapter = AdapterPalsu((opsi) async {
      await token.hapus();
      return jawabanJson(401, problem(401, GalatApi.tipeTokenKedaluwarsa));
    });
    klien = buat(adapter);
    await expectLater(klien.dio.get<void>('/api/v1/daftar-tunggu'), throwsA(isA<DioException>()));
    expect(adapter.permintaan, hasLength(1));
  });

  test('request yang diulang dan gagal lagi meneruskan error barunya', () async {
    final adapter = AdapterPalsu((opsi) async {
      if (opsi.path == '/api/v1/auth/refresh') return jawabanJson(200, {'access_token': 'akses-baru'});
      if (bearer(opsi) == 'Bearer akses-lama') return jawabanJson(401, problem(401, GalatApi.tipeTokenKedaluwarsa));
      return jawabanJson(403, problem(403, GalatApi.tipeAksesDitolak));
    });
    await expectLater(
      buat(adapter).dio.get<void>('/api/v1/daftar-tunggu'),
      throwsA(isA<DioException>().having((e) => e.response?.statusCode, 'status', 403)),
    );
  });

  test('unggahan FormData dibuat ulang saat request diulang', () async {
    final adapter = AdapterPalsu((opsi) async {
      if (opsi.path == '/api/v1/auth/refresh') return jawabanJson(200, {'access_token': 'akses-baru'});
      if (bearer(opsi) == 'Bearer akses-lama') return jawabanJson(401, problem(401, GalatApi.tipeTokenKedaluwarsa));
      return jawabanJson(200, {'id_pemindaian': 'x'});
    });
    final data = FormData.fromMap({
      'jenis_alat': 'tensimeter',
      'berkas': MultipartFile.fromBytes([1, 2, 3], filename: 'a.jpg'),
    });
    final respons = await buat(adapter).dio.post<Map<String, dynamic>>('/api/v1/pemindaian', data: data);
    expect(respons.data, {'id_pemindaian': 'x'});
    expect(identical(adapter.permintaan.last.data, data), isFalse);
  });

  test('request yang tidak bisa diulang dikembalikan sebagai error aslinya', () async {
    final adapter = AdapterPalsu((opsi) async {
      if (opsi.path == '/api/v1/auth/refresh') return jawabanJson(200, {'access_token': 'akses-baru'});
      return jawabanJson(401, problem(401, GalatApi.tipeTokenKedaluwarsa));
    });
    // Stream yang sudah dibaca tidak bisa dikirim ulang.
    final data = Stream<List<int>>.fromIterable([
      [1, 2, 3],
    ]);
    await expectLater(
      buat(adapter).dio.post<void>(
        '/api/v1/pemindaian',
        data: data,
        options: Options(headers: {'Content-Length': 3}),
      ),
      throwsA(isA<DioException>()),
    );
  });

  group('keluar', () {
    test('memanggil logout dengan refresh token lalu menghapus token', () async {
      final adapter = AdapterPalsu((_) async => jawabanJson(204, null));
      await buat(adapter).keluar();
      expect(adapter.permintaan.single.path, '/api/v1/auth/logout');
      expect(bearer(adapter.permintaan.single), 'Bearer refresh-1');
      expect(await token.baca(), isNull);
    });

    test('server tidak terjangkau tetap menghapus token', () async {
      final adapter = AdapterPalsu(
        (opsi) async => throw DioException.connectionError(requestOptions: opsi, reason: 'x'),
      );
      await buat(adapter).keluar();
      expect(await token.baca(), isNull);
    });

    test('tanpa token tidak menghubungi server', () async {
      await token.hapus();
      final adapter = AdapterPalsu((_) async => jawabanJson(204, null));
      await buat(adapter).keluar();
      expect(adapter.permintaan, isEmpty);
    });
  });

  test('perbaruiAkses tanpa token mengembalikan null', () async {
    await token.hapus();
    expect(await buat(AdapterPalsu((_) async => jawabanJson(200, {}))).perbaruiAkses(), isNull);
  });

  test('tanpa adapter memakai adapter bawaan dio', () {
    final klien = KlienHttp(alamat: 'http://server', token: token, saatSesiBerakhir: () {});
    expect(klien.dio.options.baseUrl, 'http://server');
  });
}
