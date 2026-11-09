// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'faktor_response.dart';

part 'penjelasan_response.g.dart';

@JsonSerializable()
class PenjelasanResponse {
  const PenjelasanResponse({
    required this.versiModel,
    required this.faktor,
    required this.probabilitas,
  });
  
  factory PenjelasanResponse.fromJson(Map<String, Object?> json) => _$PenjelasanResponseFromJson(json);
  
  @JsonKey(name: 'versi_model')
  final String? versiModel;
  final List<FaktorResponse> faktor;
  final Map<String, num>? probabilitas;

  Map<String, Object?> toJson() => _$PenjelasanResponseToJson(this);
}
