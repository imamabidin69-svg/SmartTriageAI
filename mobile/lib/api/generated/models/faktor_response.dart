// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'faktor_response_arah.dart';

part 'faktor_response.g.dart';

@JsonSerializable()
class FaktorResponse {
  const FaktorResponse({
    required this.fitur,
    required this.label,
    required this.nilai,
    required this.kontribusi,
    required this.arah,
  });
  
  factory FaktorResponse.fromJson(Map<String, Object?> json) => _$FaktorResponseFromJson(json);
  
  final String? fitur;
  final String label;
  final dynamic nilai;

  /// Nilai SHAP untuk hasil model, atau poin aturan untuk aturan cadangan.
  final num kontribusi;

  /// Untuk sumber model: naik berarti faktor ini mendukung level yang direkomendasikan, turun berarti melawannya. Untuk sumber aturan: naik berarti menambah poin risiko; netral bila tidak ada aturan yang terpicu.
  final FaktorResponseArah arah;

  Map<String, Object?> toJson() => _$FaktorResponseToJson(this);
}
