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

  /// Mencatat observasi pasien ICU dan menilai prioritasnya.
  ///
  /// Menghitung skor NEWS2 dan peluang perburukan 6 jam dari model Random Forest, lalu memakai level yang lebih tinggi dari keduanya. Observasi pertama (awal) dan observasi yang levelnya naik dibanding level final terakhir berstatus menunggu persetujuan dokter; selain itu langsung berstatus tercatat. Nilai yang tidak wajar dikembalikan di field peringatan tanpa menolak request. Pasien yang sudah keluar ICU dibalas 409.
  @POST('/api/v1/kunjungan/{id_kunjungan}/triase')
  Future<TriaseDetail> triaseBuatTriaseKunjunganUuidIdKunjunganTriasePost({
    @Path('id_kunjungan') required String idKunjungan,
    @Body() required TriaseInput body,
  });

  /// Detail observasi beserta penjelasan penilaian
  @GET('/api/v1/triase/{id_triase}')
  Future<TriaseDetail> triaseDetailTriaseTriaseUuidIdTriaseGet({
    @Path('id_triase') required String idTriase,
  });

  /// Persetujuan dokter: menyetujui, mengoreksi, atau mengajukan review.
  ///
  /// Hanya dokter yang boleh menyetujui atau mengoreksi level; perawat hanya boleh mengajukan review. Koreksi dan ajuan review wajib beralasan minimal 5 karakter. Penilaian yang sudah final (disetujui, dikoreksi, atau tercatat), sudah digantikan observasi yang lebih baru, atau pasiennya sudah keluar ICU dibalas 409. Setiap aksi dicatat di log audit dalam transaksi yang sama.
  @POST('/api/v1/triase/{id_triase}/validasi')
  Future<TriaseDetail> triaseValidasiTriaseTriaseUuidIdTriaseValidasiPost({
    @Path('id_triase') required String idTriase,
    @Body() required ValidasiRequest body,
  });

  /// Riwayat observasi pasien.
  ///
  /// Observasi dari semua masa rawat ICU pasien, terbaru lebih dulu. Halaman berikutnya diambil dengan mengirim kursor_berikutnya sebagai parameter kursor. NIK dan nomor telepon tidak dikirim.
  ///
  /// [kursor] - Dari kursor_berikutnya halaman sebelumnya.
  @GET('/api/v1/pasien/{id_pasien}/riwayat')
  Future<RiwayatResponse> triaseRiwayatPasienPasienUuidIdPasienRiwayatGet({
    @Path('id_pasien') required String idPasien,
    @Query('ukuran') int? ukuran = 20,
    @Query('kursor') String? kursor,
  });
}
