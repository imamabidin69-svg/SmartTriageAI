// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../models/daftar_pasien_response.dart';
import '../models/kunjungan_dibuat_response.dart';
import '../models/registrasi_request.dart';
import '../models/ringkasan_eir_response.dart';
import '../models/status_kunjungan_request.dart';
import '../models/status_kunjungan_response.dart';
import '../models/tautan_eir_response.dart';

part 'kunjungan_client.g.dart';

@RestApi()
abstract class KunjunganClient {
  factory KunjunganClient(Dio dio, {String? baseUrl}) = _KunjunganClient;

  /// Mencari pasien lama.
  ///
  /// Potongan nama (tanpa membedakan huruf besar) atau NIK lengkap 16 digit. Maksimal 20 hasil. Pencarian NIK yang tidak menemukan pasien dibatasi 30 kali per 15 menit untuk setiap akun.
  ///
  /// [q] - Potongan nama pasien, atau NIK lengkap 16 digit.
  @GET('/api/v1/pasien')
  Future<DaftarPasienResponse> kunjunganCariPasienPasienGet({
    @Query('q') required String q,
  });

  /// Registrasi singkat dan pembuatan kunjungan.
  ///
  /// Pilih pasien lama lewat id_pasien, atau isi identitas pasien baru. Pasien dengan NIK yang sudah terdaftar dipakai ulang bila nama dan jenis kelaminnya sama.
  @POST('/api/v1/kunjungan')
  Future<KunjunganDibuatResponse> kunjunganRegistrasiKunjunganPost({
    @Body() required RegistrasiRequest body,
  });

  /// Menandai pasien mulai diperiksa atau selesai.
  ///
  /// Dokter mengubah status menunggu ke ditangani (pasien keluar dari daftar tunggu), ditangani ke selesai, atau menunggu ke selesai untuk pasien yang batal diperiksa. Perubahan lain dibalas 409.
  @PATCH('/api/v1/kunjungan/{id_kunjungan}/status')
  Future<StatusKunjunganResponse> kunjunganUbahStatusKunjunganUuidIdKunjunganStatusPatch({
    @Path('id_kunjungan') required String idKunjungan,
    @Body() required StatusKunjunganRequest body,
  });

  /// Membuat tautan Eir untuk kode QR.
  ///
  /// Khusus kunjungan yang masih menunggu dan risk level terakhirnya rendah. Token berlaku dua jam dan ditampilkan sebagai kode QR untuk pasien atau keluarga. Kunjungan lain dibalas 409.
  @POST('/api/v1/kunjungan/{id_kunjungan}/tautan-eir')
  Future<TautanEirResponse> kunjunganTautanEirKunjunganUuidIdKunjunganTautanEirPost({
    @Path('id_kunjungan') required String idKunjungan,
  });

  /// Membaca ringkasan Eir terakhir sebagai draf form triase.
  ///
  /// Sesi Eir terbaru untuk kunjungan ini (keputusan E1), berisi ringkasan, transkrip, dan tanda bahaya bila sesi dihentikan. Ringkasan masih draf dan wajib diperiksa perawat sebelum dipakai di form triase. 404 bila kunjungan belum punya sesi Eir.
  @GET('/api/v1/kunjungan/{id_kunjungan}/ringkasan-eir')
  Future<RingkasanEirResponse> kunjunganRingkasanEirKunjunganUuidIdKunjunganRingkasanEirGet({
    @Path('id_kunjungan') required String idKunjungan,
  });
}
