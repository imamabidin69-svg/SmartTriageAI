// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'jenis_kelamin.dart';

part 'pasien_triase.g.dart';

@JsonSerializable()
class PasienTriase {
  const PasienTriase({
    required this.idPasien,
    required this.nama,
    required this.usia,
    required this.jenisKelamin,
  });
  
  factory PasienTriase.fromJson(Map<String, Object?> json) => _$PasienTriaseFromJson(json);
  
  @JsonKey(name: 'id_pasien')
  final String idPasien;
  final String nama;
  final int? usia;
  @JsonKey(name: 'jenis_kelamin')
  final JenisKelamin jenisKelamin;

  Map<String, Object?> toJson() => _$PasienTriaseToJson(this);
}
