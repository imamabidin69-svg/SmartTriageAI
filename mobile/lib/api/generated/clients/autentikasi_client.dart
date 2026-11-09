// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../models/ganti_password_request.dart';
import '../models/login_request.dart';
import '../models/pengguna_response.dart';
import '../models/sesi_response.dart';
import '../models/x_client.dart';

part 'autentikasi_client.g.dart';

@RestApi()
abstract class AutentikasiClient {
  factory AutentikasiClient(Dio dio, {String? baseUrl}) = _AutentikasiClient;

  /// Masuk dengan email dan password.
  ///
  /// [xClient] - Jenis klien. Tanpa header ini klien dianggap web dan token disimpan di cookie HttpOnly.
  @POST('/api/v1/auth/login')
  Future<SesiResponse> authLoginLoginPost({
    @Body() required LoginRequest body,
    @Header('X-Client') XClient? xClient = XClient.web,
  });

  /// Memperbarui access token dengan refresh token
  @POST('/api/v1/auth/refresh')
  Future<SesiResponse> authRefreshRefreshPost();

  /// Keluar.
  ///
  /// Memakai refresh token supaya tetap berhasil walau access token sudah kedaluwarsa.
  @POST('/api/v1/auth/logout')
  Future<void> authLogoutLogoutPost();

  /// Profil pengguna yang sedang masuk
  @GET('/api/v1/auth/me')
  Future<PenggunaResponse> authMeMeGet();

  /// Mengganti password sendiri.
  ///
  /// Password baru 8-128 karakter dan harus berbeda dari password lama. Password lama yang salah dibatasi 5 kali per 15 menit. Token yang sudah terbit tetap berlaku sampai kedaluwarsa.
  @PATCH('/api/v1/auth/password')
  Future<void> authGantiPasswordPasswordPatch({
    @Body() required GantiPasswordRequest body,
  });
}
