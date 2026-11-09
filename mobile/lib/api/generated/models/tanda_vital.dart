// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'tanda_vital.g.dart';

/// Batas di sini adalah nilai yang mungkin dicatat (sama dengan CHECK di basis data).
///
/// Nilai yang mungkin tetapi tidak wajar, misalnya saturasi 85%, tetap diterima lalu ditandai.
/// sebagai peringatan (Desain 2.3).
@JsonSerializable()
class TandaVital {
  const TandaVital({
    required this.tdSistolik,
    required this.tdDiastolik,
    required this.nadi,
    required this.lajuNapas,
    required this.suhu,
    required this.saturasi,
  });
  
  factory TandaVital.fromJson(Map<String, Object?> json) => _$TandaVitalFromJson(json);
  
  @JsonKey(name: 'td_sistolik')
  final int tdSistolik;
  @JsonKey(name: 'td_diastolik')
  final int tdDiastolik;
  final int nadi;
  @JsonKey(name: 'laju_napas')
  final int lajuNapas;
  final dynamic suhu;
  final dynamic saturasi;

  Map<String, Object?> toJson() => _$TandaVitalToJson(this);
}
