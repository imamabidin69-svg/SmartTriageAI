// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'tanda_vital.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

TandaVital _$TandaVitalFromJson(Map<String, dynamic> json) => TandaVital(
  tdSistolik: (json['td_sistolik'] as num).toInt(),
  tdDiastolik: (json['td_diastolik'] as num).toInt(),
  nadi: (json['nadi'] as num).toInt(),
  lajuNapas: (json['laju_napas'] as num).toInt(),
  suhu: json['suhu'],
  saturasi: json['saturasi'],
);

Map<String, dynamic> _$TandaVitalToJson(TandaVital instance) =>
    <String, dynamic>{
      'td_sistolik': instance.tdSistolik,
      'td_diastolik': instance.tdDiastolik,
      'nadi': instance.nadi,
      'laju_napas': instance.lajuNapas,
      'suhu': instance.suhu,
      'saturasi': instance.saturasi,
    };
