// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'tanda_vital_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

TandaVitalResponse _$TandaVitalResponseFromJson(Map<String, dynamic> json) =>
    TandaVitalResponse(
      tdSistolik: (json['td_sistolik'] as num).toInt(),
      tdDiastolik: (json['td_diastolik'] as num).toInt(),
      nadi: (json['nadi'] as num).toInt(),
      lajuNapas: (json['laju_napas'] as num).toInt(),
      suhu: json['suhu'] as num,
      saturasi: json['saturasi'] as num,
    );

Map<String, dynamic> _$TandaVitalResponseToJson(TandaVitalResponse instance) =>
    <String, dynamic>{
      'td_sistolik': instance.tdSistolik,
      'td_diastolik': instance.tdDiastolik,
      'nadi': instance.nadi,
      'laju_napas': instance.lajuNapas,
      'suhu': instance.suhu,
      'saturasi': instance.saturasi,
    };
