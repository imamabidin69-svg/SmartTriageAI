// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'pasien_peringatan.g.dart';

@JsonSerializable()
class PasienPeringatan {
  const PasienPeringatan({
    required this.idPasien,
    required this.nama,
  });
  
  factory PasienPeringatan.fromJson(Map<String, Object?> json) => _$PasienPeringatanFromJson(json);
  
  @JsonKey(name: 'id_pasien')
  final String idPasien;
  final String nama;

  Map<String, Object?> toJson() => _$PasienPeringatanToJson(this);
}
