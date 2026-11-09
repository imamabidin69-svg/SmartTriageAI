// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'pengguna_ringkas.g.dart';

@JsonSerializable()
class PenggunaRingkas {
  const PenggunaRingkas({
    required this.idPengguna,
    required this.nama,
  });
  
  factory PenggunaRingkas.fromJson(Map<String, Object?> json) => _$PenggunaRingkasFromJson(json);
  
  @JsonKey(name: 'id_pengguna')
  final String idPengguna;
  final String nama;

  Map<String, Object?> toJson() => _$PenggunaRingkasToJson(this);
}
