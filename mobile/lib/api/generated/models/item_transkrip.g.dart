// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'item_transkrip.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ItemTranskrip _$ItemTranskripFromJson(Map<String, dynamic> json) =>
    ItemTranskrip(
      peran: ItemTranskripPeran.fromJson(json['peran'] as String),
      teks: json['teks'] as String,
      waktu: DateTime.parse(json['waktu'] as String),
    );

Map<String, dynamic> _$ItemTranskripToJson(ItemTranskrip instance) =>
    <String, dynamic>{
      'peran': _$ItemTranskripPeranEnumMap[instance.peran]!,
      'teks': instance.teks,
      'waktu': instance.waktu.toIso8601String(),
    };

const _$ItemTranskripPeranEnumMap = {
  ItemTranskripPeran.eir: 'eir',
  ItemTranskripPeran.pengisi: 'pengisi',
  ItemTranskripPeran.$unknown: r'$unknown',
};
