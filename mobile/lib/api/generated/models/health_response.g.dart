// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'health_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

HealthResponse _$HealthResponseFromJson(Map<String, dynamic> json) =>
    HealthResponse(
      status: HealthResponseStatus.fromJson(json['status'] as String),
      komponen: (json['komponen'] as Map<String, dynamic>).map(
        (k, e) => MapEntry(k, KomponenKomponen.fromJson(e as String)),
      ),
    );

Map<String, dynamic> _$HealthResponseToJson(HealthResponse instance) =>
    <String, dynamic>{
      'status': _$HealthResponseStatusEnumMap[instance.status]!,
      'komponen': instance.komponen.map(
        (k, e) => MapEntry(k, _$KomponenKomponenEnumMap[e]!),
      ),
    };

const _$HealthResponseStatusEnumMap = {
  HealthResponseStatus.ok: 'ok',
  HealthResponseStatus.degraded: 'degraded',
  HealthResponseStatus.gagal: 'gagal',
  HealthResponseStatus.$unknown: r'$unknown',
};

const _$KomponenKomponenEnumMap = {
  KomponenKomponen.ok: 'ok',
  KomponenKomponen.gagal: 'gagal',
  KomponenKomponen.$unknown: r'$unknown',
};
