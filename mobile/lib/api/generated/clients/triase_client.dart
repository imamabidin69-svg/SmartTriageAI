// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../models/riwayat_response.dart';
import '../models/triase_detail.dart';
import '../models/triase_input.dart';
import '../models/validasi_request.dart';

part 'triase_client.g.dart';

@RestApi()
abstract class TriaseClient {
  factory TriaseClient(Dio dio, {String? baseUrl}) = _TriaseClient;

  /// Input triase dan rekomendasi risk level.
  ///
  /// Menyimpan triase berstatus menunggu validasi beserta rekomendasi risk level dan tiga faktor penjelas. Triase pertama pada kunjungan dicatat sebagai awal, berikutnya sebagai ulang. Nilai tanda vital yang tidak wajar dikembalikan di field peringatan tanpa menolak request.
  @POST('/api/v1/kunjungan/{id_kunjungan}/triase')
  Future<TriaseDetail> triaseBuatTriaseKunjunganUuidIdKunjunganTriasePost({
    @Path('id_kunjungan') required String idKunjungan,
    @Body() required TriaseInput body,
  });

  /// Detail triase beserta penjelasan rekomendasi
  @GET('/api/v1/triase/{id_triase}')
  Future<TriaseDetail> triaseDetailTriaseTriaseUuidIdTriaseGet({
    @Path('id_triase') required String idTriase,
  });

  /// Menyetujui, mengoreksi, atau mengajukan review hasil triase.
  ///
  /// Perawat boleh menyetujui hasil non-kritis atau mengajukan review; dokter boleh menyetujui atau mengoreksi semua tingkat. Koreksi dan ajuan review wajib beralasan minimal 5 karakter. Triase yang sudah disetujui atau dikoreksi, sudah digantikan triase ulang, atau kunjungannya sudah selesai dibalas 409. Setiap aksi dicatat di log audit dalam transaksi yang sama.
  @POST('/api/v1/triase/{id_triase}/validasi')
  Future<TriaseDetail> triaseValidasiTriaseTriaseUuidIdTriaseValidasiPost({
    @Path('id_triase') required String idTriase,
    @Body() required ValidasiRequest body,
  });

  /// Riwayat triase pasien.
  ///
  /// Triase awal dan ulang dari semua kunjungan pasien, terbaru lebih dulu. Halaman berikutnya diambil dengan mengirim kursor_berikutnya sebagai parameter kursor. NIK dan nomor telepon tidak dikirim.
  ///
  /// [kursor] - Dari kursor_berikutnya halaman sebelumnya.
  @GET('/api/v1/pasien/{id_pasien}/riwayat')
  Future<RiwayatResponse> triaseRiwayatPasienPasienUuidIdPasienRiwayatGet({
    @Path('id_pasien') required String idPasien,
    @Query('ukuran') int? ukuran = 20,
    @Query('kursor') String? kursor,
  });
}
