// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'peran.dart';

part 'pengguna_response.g.dart';

@JsonSerializable()
class PenggunaResponse {
  const PenggunaResponse({
    required this.idPengguna,
    required this.nama,
    required this.email,
    required this.peran,
    required this.isActive,
  });
  
  factory PenggunaResponse.fromJson(Map<String, Object?> json) => _$PenggunaResponseFromJson(json);
  
  @JsonKey(name: 'id_pengguna')
  final String idPengguna;
  final String nama;
  final String email;
  final Peran peran;
  @JsonKey(name: 'is_active')
  final bool isActive;

  Map<String, Object?> toJson() => _$PenggunaResponseToJson(this);
}
