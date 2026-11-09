// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'pasien_ringkas.dart';

part 'daftar_pasien_response.g.dart';

@JsonSerializable()
class DaftarPasienResponse {
  const DaftarPasienResponse({
    required this.items,
  });
  
  factory DaftarPasienResponse.fromJson(Map<String, Object?> json) => _$DaftarPasienResponseFromJson(json);
  
  final List<PasienRingkas> items;

  Map<String, Object?> toJson() => _$DaftarPasienResponseToJson(this);
}
