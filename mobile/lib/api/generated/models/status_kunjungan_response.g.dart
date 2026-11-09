// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'status_kunjungan_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

StatusKunjunganResponse _$StatusKunjunganResponseFromJson(
  Map<String, dynamic> json,
) => StatusKunjunganResponse(
  idKunjungan: json['id_kunjungan'] as String,
  status: StatusKunjungan.fromJson(json['status'] as String),
  waktuDitangani: json['waktu_ditangani'] == null
      ? null
      : DateTime.parse(json['waktu_ditangani'] as String),
);

Map<String, dynamic> _$StatusKunjunganResponseToJson(
  StatusKunjunganResponse instance,
) => <String, dynamic>{
  'id_kunjungan': instance.idKunjungan,
  'status': _$StatusKunjunganEnumMap[instance.status]!,
  'waktu_ditangani': instance.waktuDitangani?.toIso8601String(),
};

const _$StatusKunjunganEnumMap = {
  StatusKunjungan.menunggu: 'menunggu',
  StatusKunjungan.ditangani: 'ditangani',
  StatusKunjungan.selesai: 'selesai',
  StatusKunjungan.$unknown: r'$unknown',
};
