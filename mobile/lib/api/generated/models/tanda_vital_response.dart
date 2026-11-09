// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'tanda_vital_response.g.dart';

@JsonSerializable()
class TandaVitalResponse {
  const TandaVitalResponse({
    required this.tdSistolik,
    required this.tdDiastolik,
    required this.nadi,
    required this.lajuNapas,
    required this.suhu,
    required this.saturasi,
  });
  
  factory TandaVitalResponse.fromJson(Map<String, Object?> json) => _$TandaVitalResponseFromJson(json);
  
  @JsonKey(name: 'td_sistolik')
  final int tdSistolik;
  @JsonKey(name: 'td_diastolik')
  final int tdDiastolik;
  final int nadi;
  @JsonKey(name: 'laju_napas')
  final int lajuNapas;
  final num suhu;
  final num saturasi;

  Map<String, Object?> toJson() => _$TandaVitalResponseToJson(this);
}
