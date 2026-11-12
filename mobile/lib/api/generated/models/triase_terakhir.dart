// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'jenis_triase.dart';
import 'risk_level.dart';
import 'status_validasi.dart';

part 'triase_terakhir.g.dart';

@JsonSerializable()
class TriaseTerakhir {
  const TriaseTerakhir({
    required this.idTriase,
    required this.jenis,
    required this.riskLevel,
    required this.statusValidasi,
    required this.skorNews2,
    required this.peluangPerburukan,
    required this.waktuTriase,
  });
  
  factory TriaseTerakhir.fromJson(Map<String, Object?> json) => _$TriaseTerakhirFromJson(json);
  
  @JsonKey(name: 'id_triase')
  final String idTriase;
  final JenisTriase jenis;
  @JsonKey(name: 'risk_level')
  final RiskLevel riskLevel;
  @JsonKey(name: 'status_validasi')
  final StatusValidasi statusValidasi;
  @JsonKey(name: 'skor_news2')
  final int skorNews2;
  @JsonKey(name: 'peluang_perburukan')
  final num? peluangPerburukan;
  @JsonKey(name: 'waktu_triase')
  final DateTime waktuTriase;

  Map<String, Object?> toJson() => _$TriaseTerakhirToJson(this);
}
