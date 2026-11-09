// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'status_kunjungan.dart';

part 'status_kunjungan_response.g.dart';

@JsonSerializable()
class StatusKunjunganResponse {
  const StatusKunjunganResponse({
    required this.idKunjungan,
    required this.status,
    required this.waktuDitangani,
  });
  
  factory StatusKunjunganResponse.fromJson(Map<String, Object?> json) => _$StatusKunjunganResponseFromJson(json);
  
  @JsonKey(name: 'id_kunjungan')
  final String idKunjungan;
  final StatusKunjungan status;
  @JsonKey(name: 'waktu_ditangani')
  final DateTime? waktuDitangani;

  Map<String, Object?> toJson() => _$StatusKunjunganResponseToJson(this);
}
