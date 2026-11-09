// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'daftar_peringatan_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

DaftarPeringatanResponse _$DaftarPeringatanResponseFromJson(
  Map<String, dynamic> json,
) => DaftarPeringatanResponse(
  items: (json['items'] as List<dynamic>)
      .map((e) => ItemPeringatan.fromJson(e as Map<String, dynamic>))
      .toList(),
);

Map<String, dynamic> _$DaftarPeringatanResponseToJson(
  DaftarPeringatanResponse instance,
) => <String, dynamic>{'items': instance.items};
