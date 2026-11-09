// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'item_peringatan_jenis.dart';
import 'pasien_peringatan.dart';
import 'risk_level.dart';

part 'item_peringatan.g.dart';

@JsonSerializable()
class ItemPeringatan {
  const ItemPeringatan({
    required this.jenis,
    required this.idKunjungan,
    required this.idTriase,
    required this.idSesi,
    required this.pasien,
    required this.riskLevel,
    required this.alasan,
    required this.waktu,
  });
  
  factory ItemPeringatan.fromJson(Map<String, Object?> json) => _$ItemPeringatanFromJson(json);
  
  final ItemPeringatanJenis jenis;
  @JsonKey(name: 'id_kunjungan')
  final String idKunjungan;
  @JsonKey(name: 'id_triase')
  final String? idTriase;
  @JsonKey(name: 'id_sesi')
  final String? idSesi;
  final PasienPeringatan pasien;
  @JsonKey(name: 'risk_level')
  final RiskLevel? riskLevel;
  final String alasan;
  final DateTime waktu;

  Map<String, Object?> toJson() => _$ItemPeringatanToJson(this);
}
