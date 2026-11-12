// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'hasil_lab.g.dart';

/// Hasil laboratorium terakhir. Semuanya boleh kosong; yang kosong diisi median oleh model.
@JsonSerializable()
class HasilLab {
  const HasilLab({
    required this.laktat,
    required this.kreatinin,
    required this.trombosit,
    required this.leukosit,
    required this.bilirubin,
  });
  
  factory HasilLab.fromJson(Map<String, Object?> json) => _$HasilLabFromJson(json);
  
  /// mmol/L
  final dynamic laktat;

  /// mg/dL
  final dynamic kreatinin;

  /// ribu/µL
  final int? trombosit;

  /// ribu/µL
  final dynamic leukosit;

  /// mg/dL
  final dynamic bilirubin;

  Map<String, Object?> toJson() => _$HasilLabToJson(this);
}
