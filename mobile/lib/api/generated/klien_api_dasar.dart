// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:dio/dio.dart';

import 'clients/autentikasi_client.dart';
import 'clients/sistem_client.dart';
import 'clients/kunjungan_client.dart';
import 'clients/triase_client.dart';
import 'clients/pemindaian_client.dart';
import 'clients/antrean_client.dart';

/// SmartTriage AI API `v1.0.0`
class KlienApiDasar {
  KlienApiDasar(
    Dio dio, {
    String? baseUrl,
  })  : _dio = dio,
        _baseUrl = baseUrl;

  final Dio _dio;
  final String? _baseUrl;

  static String get version => '1.0.0';

  AutentikasiClient? _autentikasi;
  SistemClient? _sistem;
  KunjunganClient? _kunjungan;
  TriaseClient? _triase;
  PemindaianClient? _pemindaian;
  AntreanClient? _antrean;

  AutentikasiClient get autentikasi => _autentikasi ??= AutentikasiClient(_dio, baseUrl: _baseUrl);

  SistemClient get sistem => _sistem ??= SistemClient(_dio, baseUrl: _baseUrl);

  KunjunganClient get kunjungan => _kunjungan ??= KunjunganClient(_dio, baseUrl: _baseUrl);

  TriaseClient get triase => _triase ??= TriaseClient(_dio, baseUrl: _baseUrl);

  PemindaianClient get pemindaian => _pemindaian ??= PemindaianClient(_dio, baseUrl: _baseUrl);

  AntreanClient get antrean => _antrean ??= AntreanClient(_dio, baseUrl: _baseUrl);
}
