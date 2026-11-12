// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'status_kunjungan_request_status.dart';

part 'status_kunjungan_request.g.dart';

@JsonSerializable()
class StatusKunjunganRequest {
  const StatusKunjunganRequest({
    required this.status,
  });
  
  factory StatusKunjunganRequest.fromJson(Map<String, Object?> json) => _$StatusKunjunganRequestFromJson(json);
  
  /// ditangani saat pasien mulai menjalani tindakan atau operasi, menunggu saat kembali dipantau setelah tindakan, selesai saat pasien keluar ICU (pindah ruangan, pulang, atau meninggal).
  final StatusKunjunganRequestStatus status;

  Map<String, Object?> toJson() => _$StatusKunjunganRequestToJson(this);
}
