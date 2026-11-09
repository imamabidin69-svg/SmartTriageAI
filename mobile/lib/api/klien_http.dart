import 'package:dio/dio.dart';

import '../konfigurasi.dart';
import 'galat_api.dart';
import 'penyimpanan_token.dart';

/// Dio untuk REST API SmartTriage AI dengan token Bearer dan refresh otomatis (Desain 2.1).
///
/// Bila access token ditolak karena kedaluwarsa, refresh token dipakai untuk meminta access token baru lalu
/// request diulang sekali. Bila refresh juga ditolak, token dihapus dan [saatSesiBerakhir] dipanggil supaya
/// aplikasi kembali ke halaman login.
class KlienHttp {
  KlienHttp({required String alamat, required this.token, required this.saatSesiBerakhir, HttpClientAdapter? adapter}) {
    final opsi = BaseOptions(
      baseUrl: alamat,
      connectTimeout: batasWaktuRequest,
      receiveTimeout: batasWaktuRequest,
      sendTimeout: batasWaktuRequest,
    );
    dio = Dio(opsi);
    _polos = Dio(opsi);
    if (adapter != null) {
      dio.httpClientAdapter = adapter;
      _polos.httpClientAdapter = adapter;
    }
    dio.interceptors.add(_PenjagaToken(this));
  }

  /// Dio yang dipakai klien hasil generate. Header Authorization ditambahkan otomatis.
  late final Dio dio;

  /// Dio tanpa interceptor untuk refresh, logout, dan pengulangan request. Pengulangan sengaja tidak lewat
  /// [dio] karena antrean interceptor masih menunggu request yang sedang ditangani.
  late final Dio _polos;

  final PenyimpananToken token;
  final void Function() saatSesiBerakhir;

  Future<String?>? _refreshBerjalan;

  /// Meminta access token baru. Beberapa request yang gagal bersamaan memakai satu refresh yang sama.
  Future<String?> perbaruiAkses() => _refreshBerjalan ??= _perbarui().whenComplete(() => _refreshBerjalan = null);

  Future<String?> _perbarui() async {
    final tersimpan = await token.baca();
    if (tersimpan == null) return null;
    try {
      final respons = await _polos.post<Map<String, dynamic>>(
        '/api/v1/auth/refresh',
        options: Options(headers: {'Authorization': 'Bearer ${tersimpan.refresh}'}),
      );
      final akses = respons.data?['access_token'];
      if (akses is! String) return null;
      await token.gantiAkses(akses);
      return akses;
    } on DioException catch (galat) {
      // Refresh token kedaluwarsa atau akun dinonaktifkan: sesi berakhir. Gangguan jaringan tidak menghapus sesi.
      if (galat.response?.statusCode == 401) {
        await token.hapus();
        saatSesiBerakhir();
      }
      return null;
    }
  }

  /// Logout di server memakai refresh token. Gagal pun tidak masalah karena token lokal tetap dihapus.
  Future<void> keluar() async {
    final tersimpan = await token.baca();
    await token.hapus();
    if (tersimpan == null) return;
    try {
      await _polos.post<void>(
        '/api/v1/auth/logout',
        options: Options(headers: {'Authorization': 'Bearer ${tersimpan.refresh}'}),
      );
    } on DioException {
      // Server tidak menyimpan sesi untuk klien mobile, jadi cukup token lokal yang dihapus.
    }
  }

  Future<Response<dynamic>> _ulangi(RequestOptions opsi, String akses) {
    final data = opsi.data;
    return _polos.fetch<dynamic>(
      opsi.copyWith(
        headers: {...opsi.headers, 'Authorization': 'Bearer $akses'},
        // FormData (foto pemindaian) hanya bisa dikirim sekali, jadi dibuat salinannya.
        data: data is FormData ? data.clone() : data,
      ),
    );
  }
}

class _PenjagaToken extends QueuedInterceptor {
  _PenjagaToken(this.klien);

  final KlienHttp klien;

  static const _tipePerluRefresh = {GalatApi.tipeTokenKedaluwarsa, GalatApi.tipeTidakTerautentikasi};

  @override
  Future<void> onRequest(RequestOptions options, RequestInterceptorHandler handler) async {
    if (!options.headers.containsKey('Authorization')) {
      final tersimpan = await klien.token.baca();
      if (tersimpan != null) options.headers['Authorization'] = 'Bearer ${tersimpan.akses}';
    }
    handler.next(options);
  }

  @override
  Future<void> onError(DioException err, ErrorInterceptorHandler handler) async {
    final respons = err.response;
    final tipe = respons?.data is Map ? (respons!.data as Map)['type'] : null;
    final terkirim = err.requestOptions.headers['Authorization'];
    if (respons?.statusCode == 401 && tipe == GalatApi.tipeSesiBerakhir && terkirim != null) {
      // Akun dinonaktifkan admin atau sesi dicabut: tidak bisa diperbarui, harus login ulang.
      await klien.token.hapus();
      klien.saatSesiBerakhir();
      handler.next(err);
      return;
    }
    if (respons?.statusCode != 401 || !_tipePerluRefresh.contains(tipe) || terkirim == null) {
      handler.next(err);
      return;
    }
    // Request lain mungkin sudah memperbarui token selagi request ini menunggu di antrean.
    final tersimpan = await klien.token.baca();
    String? akses = tersimpan?.akses;
    if (akses == null) {
      handler.next(err);
      return;
    }
    if (terkirim == 'Bearer $akses') akses = await klien.perbaruiAkses();
    if (akses == null) {
      handler.next(err);
      return;
    }
    try {
      handler.resolve(await klien._ulangi(err.requestOptions, akses));
    } on DioException catch (galatUlang) {
      handler.next(galatUlang);
    } catch (_) {
      // Request yang tidak bisa diulang tetap dikembalikan sebagai error aslinya, bukan menggantung.
      handler.next(err);
    }
  }
}
