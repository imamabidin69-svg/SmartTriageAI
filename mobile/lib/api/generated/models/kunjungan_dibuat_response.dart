// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'status_kunjungan.dart';

part 'kunjungan_dibuat_response.g.dart';

@JsonSerializable()
class KunjunganDibuatResponse {
  const KunjunganDibuatResponse({
    required this.idKunjungan,
    required this.idPasien,
    required this.pasienBaru,
    required this.status,
    required this.waktuDatang,
  });
  
  factory KunjunganDibuatResponse.fromJson(Map<String, Object?> json) => _$KunjunganDibuatResponseFromJson(json);
  
  @JsonKey(name: 'id_kunjungan')
  final String idKunjungan;
  @JsonKey(name: 'id_pasien')
  final String idPasien;
  @JsonKey(name: 'pasien_baru')
  final bool pasienBaru;
  final StatusKunjungan status;
  @JsonKey(name: 'waktu_datang')
  final DateTime waktuDatang;

  Map<String, Object?> toJson() => _$KunjunganDibuatResponseToJson(this);
}
