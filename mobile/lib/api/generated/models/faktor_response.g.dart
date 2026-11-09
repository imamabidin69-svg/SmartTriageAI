// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'faktor_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

FaktorResponse _$FaktorResponseFromJson(Map<String, dynamic> json) =>
    FaktorResponse(
      fitur: json['fitur'] as String?,
      label: json['label'] as String,
      nilai: json['nilai'],
      kontribusi: json['kontribusi'] as num,
      arah: FaktorResponseArah.fromJson(json['arah'] as String),
    );

Map<String, dynamic> _$FaktorResponseToJson(FaktorResponse instance) =>
    <String, dynamic>{
      'fitur': instance.fitur,
      'label': instance.label,
      'nilai': instance.nilai,
      'kontribusi': instance.kontribusi,
      'arah': _$FaktorResponseArahEnumMap[instance.arah]!,
    };

const _$FaktorResponseArahEnumMap = {
  FaktorResponseArah.naik: 'naik',
  FaktorResponseArah.turun: 'turun',
  FaktorResponseArah.netral: 'netral',
  FaktorResponseArah.$unknown: r'$unknown',
};
