// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'faktor_response.dart';
import 'risk_level.dart';

part 'penjelasan_response.g.dart';

@JsonSerializable()
class PenjelasanResponse {
  const PenjelasanResponse({
    required this.versiModel,
    required this.skorNews2,
    required this.levelNews2,
    required this.komponenNews2,
    required this.peluangPerburukan,
    required this.levelModel,
    required this.faktor,
  });
  
  factory PenjelasanResponse.fromJson(Map<String, Object?> json) => _$PenjelasanResponseFromJson(json);
  
  @JsonKey(name: 'versi_model')
  final String? versiModel;
  @JsonKey(name: 'skor_news2')
  final int skorNews2;
  @JsonKey(name: 'level_news2')
  final RiskLevel levelNews2;

  /// Parameter NEWS2 yang menyumbang poin.
  @JsonKey(name: 'komponen_news2')
  final List<FaktorResponse> komponenNews2;

  /// Peluang memburuk dalam 6 jam (0-1); null tanpa model.
  @JsonKey(name: 'peluang_perburukan')
  final num? peluangPerburukan;
  @JsonKey(name: 'level_model')
  final RiskLevel? levelModel;

  /// Tiga faktor SHAP terbesar dari model; kosong tanpa model.
  final List<FaktorResponse> faktor;

  Map<String, Object?> toJson() => _$PenjelasanResponseToJson(this);
}
