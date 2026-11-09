// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'dart:convert';
import 'dart:io';

import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../models/hasil_pemindaian_response.dart';
import '../models/jenis_alat.dart';

part 'pemindaian_client.g.dart';

@RestApi()
abstract class PemindaianClient {
  factory PemindaianClient(Dio dio, {String? baseUrl}) = _PemindaianClient;

  /// Membaca angka dari foto layar alat.
  ///
  /// Body multipart berisi jenis_alat dan berkas (foto JPEG atau PNG maksimal 5 MB). Foto hanya diproses di memori lalu dibuang. Kolom diisi bila keyakinan model mencapai ambang konfigurasi dan nilainya wajar; selebihnya null untuk diisi manual. Kirim id_pemindaian lewat form triase setelah nilai dikonfirmasi.
  ///
  /// [berkas] - Foto layar alat (JPEG atau PNG, maksimal 5 MB).
  @MultiPart()
  @POST('/api/v1/pemindaian')
  Future<HasilPemindaianResponse> pemindaianPindaiPemindaianPost({
    @Part(name: 'jenis_alat') required JenisAlat jenisAlat,
    @Part(name: 'berkas') required File berkas,
  });
}
