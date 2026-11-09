// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../models/daftar_peringatan_response.dart';
import '../models/daftar_tunggu_response.dart';

part 'antrean_client.g.dart';

@RestApi()
abstract class AntreanClient {
  factory AntreanClient(Dio dio, {String? baseUrl}) = _AntreanClient;

  /// Daftar tunggu pasien beserta penanda triase ulang.
  ///
  /// Semua kunjungan berstatus menunggu beserta triase terakhirnya. Lama menunggu dihitung sejak triase terakhir (atau sejak datang bila belum ditriase) dan dibandingkan dengan batas per level dari konfigurasi. Urutan: kritis, belum ditriase, lewat batas, level, lalu lama menunggu. ringkasan_eir_siap bernilai true bila sesi Eir terakhir selesai dengan ringkasan dan belum ada triase sesudahnya.
  @GET('/api/v1/daftar-tunggu')
  Future<DaftarTungguResponse> antreanDaftarTungguDaftarTungguGet();

  /// Peringatan kritis, level naik, dan tanda bahaya Eir.
  ///
  /// Triase kritis yang belum divalidasi, triase ulang yang levelnya naik dan belum divalidasi, serta sesi Eir yang dihentikan karena tanda bahaya tetapi belum diikuti triase baru. Hanya kunjungan yang masih menunggu.
  @GET('/api/v1/peringatan')
  Future<DaftarPeringatanResponse> antreanPeringatanPeringatanGet();
}
