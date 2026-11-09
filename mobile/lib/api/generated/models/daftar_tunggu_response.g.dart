// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'daftar_tunggu_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

DaftarTungguResponse _$DaftarTungguResponseFromJson(
  Map<String, dynamic> json,
) => DaftarTungguResponse(
  items: (json['items'] as List<dynamic>)
      .map((e) => ItemDaftarTunggu.fromJson(e as Map<String, dynamic>))
      .toList(),
  waktuServer: DateTime.parse(json['waktu_server'] as String),
);

Map<String, dynamic> _$DaftarTungguResponseToJson(
  DaftarTungguResponse instance,
) => <String, dynamic>{
  'items': instance.items,
  'waktu_server': instance.waktuServer.toIso8601String(),
};
