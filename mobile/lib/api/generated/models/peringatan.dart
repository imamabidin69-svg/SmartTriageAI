// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'peringatan.g.dart';

/// Peringatan yang tidak menolak request, misalnya nilai tanda vital yang tidak wajar (Desain 2.3).
@JsonSerializable()
class Peringatan {
  const Peringatan({
    required this.field,
    required this.pesan,
  });
  
  factory Peringatan.fromJson(Map<String, Object?> json) => _$PeringatanFromJson(json);
  
  /// Path field yang bersangkutan, misalnya tanda_vital.saturasi.
  final String? field;
  final String pesan;

  Map<String, Object?> toJson() => _$PeringatanToJson(this);
}
