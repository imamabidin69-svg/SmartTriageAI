// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'kunjungan_riwayat.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

KunjunganRiwayat _$KunjunganRiwayatFromJson(Map<String, dynamic> json) =>
    KunjunganRiwayat(
      idKunjungan: json['id_kunjungan'] as String,
      waktuDatang: DateTime.parse(json['waktu_datang'] as String),
      waktuDitangani: json['waktu_ditangani'] == null
          ? null
          : DateTime.parse(json['waktu_ditangani'] as String),
      status: StatusKunjungan.fromJson(json['status'] as String),
    );

Map<String, dynamic> _$KunjunganRiwayatToJson(KunjunganRiwayat instance) =>
    <String, dynamic>{
      'id_kunjungan': instance.idKunjungan,
      'waktu_datang': instance.waktuDatang.toIso8601String(),
      'waktu_ditangani': instance.waktuDitangani?.toIso8601String(),
      'status': _$StatusKunjunganEnumMap[instance.status]!,
    };

const _$StatusKunjunganEnumMap = {
  StatusKunjungan.menunggu: 'menunggu',
  StatusKunjungan.ditangani: 'ditangani',
  StatusKunjungan.selesai: 'selesai',
  StatusKunjungan.$unknown: r'$unknown',
};
