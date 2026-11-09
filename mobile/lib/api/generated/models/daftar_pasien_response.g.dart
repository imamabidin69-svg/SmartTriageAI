// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'daftar_pasien_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

DaftarPasienResponse _$DaftarPasienResponseFromJson(
  Map<String, dynamic> json,
) => DaftarPasienResponse(
  items: (json['items'] as List<dynamic>)
      .map((e) => PasienRingkas.fromJson(e as Map<String, dynamic>))
      .toList(),
);

Map<String, dynamic> _$DaftarPasienResponseToJson(
  DaftarPasienResponse instance,
) => <String, dynamic>{'items': instance.items};
