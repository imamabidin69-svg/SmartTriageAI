// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'risk_level.dart';
import 'validasi_request_aksi.dart';

part 'validasi_request.g.dart';

/// Desain Gambar 2.17. Alasan wajib minimal lima karakter untuk koreksi dan ajuan review (NFR-06).
@JsonSerializable()
class ValidasiRequest {
  const ValidasiRequest({
    required this.aksi,
    required this.riskLevel,
    required this.alasan,
  });
  
  factory ValidasiRequest.fromJson(Map<String, Object?> json) => _$ValidasiRequestFromJson(json);
  
  final ValidasiRequestAksi aksi;

  /// Level hasil koreksi. Hanya diisi untuk aksi koreksi.
  @JsonKey(name: 'risk_level')
  final RiskLevel? riskLevel;

  /// Wajib minimal 5 karakter untuk koreksi dan ajuan review. Boleh diisi saat menyetujui.
  final String? alasan;

  Map<String, Object?> toJson() => _$ValidasiRequestToJson(this);
}
