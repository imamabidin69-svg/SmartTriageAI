// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'hasil_lab_response.g.dart';

@JsonSerializable()
class HasilLabResponse {
  const HasilLabResponse({
    required this.laktat,
    required this.kreatinin,
    required this.trombosit,
    required this.leukosit,
    required this.bilirubin,
  });
  
  factory HasilLabResponse.fromJson(Map<String, Object?> json) => _$HasilLabResponseFromJson(json);
  
  final num? laktat;
  final num? kreatinin;
  final int? trombosit;
  final num? leukosit;
  final num? bilirubin;

  Map<String, Object?> toJson() => _$HasilLabResponseToJson(this);
}
