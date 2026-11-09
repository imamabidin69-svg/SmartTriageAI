// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'riwayat_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

RiwayatResponse _$RiwayatResponseFromJson(Map<String, dynamic> json) =>
    RiwayatResponse(
      pasien: PasienTriase.fromJson(json['pasien'] as Map<String, dynamic>),
      items: (json['items'] as List<dynamic>)
          .map((e) => ItemRiwayat.fromJson(e as Map<String, dynamic>))
          .toList(),
      kursorBerikutnya: json['kursor_berikutnya'] as String?,
    );

Map<String, dynamic> _$RiwayatResponseToJson(RiwayatResponse instance) =>
    <String, dynamic>{
      'pasien': instance.pasien,
      'items': instance.items,
      'kursor_berikutnya': instance.kursorBerikutnya,
    };
