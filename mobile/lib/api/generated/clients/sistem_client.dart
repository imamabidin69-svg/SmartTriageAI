// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../models/health_response.dart';

part 'sistem_client.g.dart';

@RestApi()
abstract class SistemClient {
  factory SistemClient(Dio dio, {String? baseUrl}) = _SistemClient;

  /// Pemeriksaan kesehatan aplikasi.
  ///
  /// 200 bila komponen wajib sehat (status ok atau degraded), 503 bila komponen wajib gagal.
  @GET('/api/v1/health')
  Future<HealthResponse> healthHealthHealthGet();
}
