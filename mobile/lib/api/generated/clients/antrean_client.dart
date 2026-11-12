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

  /// Papan prioritas pasien ICU.
  ///
  /// Semua pasien yang belum keluar ICU beserta penilaian terakhirnya, sudah diurutkan menurut prioritas penanganan: Kritis, belum dinilai, Tinggi, Sedang, Rendah; di level yang sama yang menunggu persetujuan dokter dan yang observasinya terlambat lebih dulu, lalu peluang perburukan dan skor NEWS2 tertinggi. Pasien yang sedang menjalani tindakan ditaruh paling bawah. Lama dihitung sejak observasi terakhir dan dibandingkan dengan interval observasi level tersebut.
  @GET('/api/v1/daftar-tunggu')
  Future<DaftarTungguResponse> antreanDaftarTungguDaftarTungguGet();

  /// Peringatan persetujuan dokter, observasi terlambat, dan informasi penting Eir.
  ///
  /// Penilaian awal atau kenaikan level yang belum disetujui dokter, observasi yang melewati intervalnya, dan informasi penting dari keluarga lewat Eir yang belum diikuti observasi baru. Hanya pasien yang masih di ICU.
  @GET('/api/v1/peringatan')
  Future<DaftarPeringatanResponse> antreanPeringatanPeringatanGet();
}
