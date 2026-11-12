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

  /// Mencatat pasien masuk ICU.
  ///
  /// Pilih pasien lama lewat id_pasien, atau isi identitas pasien baru, lalu nomor bed, asal ruangan, dan diagnosis masuk. Pasien dengan NIK yang sudah terdaftar dipakai ulang bila nama dan jenis kelaminnya sama. Bed yang masih ditempati pasien lain dibalas 422 pada field nomor_bed.
  @POST('/api/v1/kunjungan')
  Future<KunjunganDibuatResponse> kunjunganRegistrasiKunjunganPost({
    @Body() required RegistrasiRequest body,
  });

  /// Mengubah status pasien ICU.
  ///
  /// Dokter menandai pasien mulai tindakan atau operasi (ditangani), kembali dipantau setelah tindakan (menunggu), atau keluar ICU (selesai). Pasien yang sedang tindakan tetap tampil di papan prioritas di urutan paling bawah. Perubahan lain dibalas 409.
  @PATCH('/api/v1/kunjungan/{id_kunjungan}/status')
  Future<StatusKunjunganResponse> kunjunganUbahStatusKunjunganUuidIdKunjunganStatusPatch({
    @Path('id_kunjungan') required String idKunjungan,
    @Body() required StatusKunjunganRequest body,
  });

  /// Membuat tautan Eir untuk keluarga pasien.
  ///
  /// Untuk pasien yang masih di ICU, apa pun levelnya. Token berlaku dua jam dan ditampilkan sebagai kode QR untuk keluarga. Pasien yang sudah keluar ICU dibalas 409.
  @POST('/api/v1/kunjungan/{id_kunjungan}/tautan-eir')
  Future<TautanEirResponse> kunjunganTautanEirKunjunganUuidIdKunjunganTautanEirPost({
    @Path('id_kunjungan') required String idKunjungan,
  });

  /// Membaca ringkasan riwayat dari keluarga lewat Eir.
  ///
  /// Sesi Eir terbaru untuk pasien ini (keputusan E1), berisi ringkasan riwayat (kronologi, penyakit, obat rutin, alergi, informasi lain), transkrip, dan informasi penting yang ditandai. Ringkasan berasal dari keterangan keluarga dan wajib diperiksa perawat. 404 bila pasien belum punya sesi Eir.
  @GET('/api/v1/kunjungan/{id_kunjungan}/ringkasan-eir')
  Future<RingkasanEirResponse> kunjunganRingkasanEirKunjunganUuidIdKunjunganRingkasanEirGet({
    @Path('id_kunjungan') required String idKunjungan,
  });
}
