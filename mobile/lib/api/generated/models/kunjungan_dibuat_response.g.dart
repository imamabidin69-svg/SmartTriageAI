// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'kunjungan_dibuat_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

KunjunganDibuatResponse _$KunjunganDibuatResponseFromJson(
  Map<String, dynamic> json,
) => KunjunganDibuatResponse(
  idKunjungan: json['id_kunjungan'] as String,
  idPasien: json['id_pasien'] as String,
  pasienBaru: json['pasien_baru'] as bool,
  status: StatusKunjungan.fromJson(json['status'] as String),
  waktuDatang: DateTime.parse(json['waktu_datang'] as String),
);

Map<String, dynamic> _$KunjunganDibuatResponseToJson(
  KunjunganDibuatResponse instance,
) => <String, dynamic>{
  'id_kunjungan': instance.idKunjungan,
  'id_pasien': instance.idPasien,
  'pasien_baru': instance.pasienBaru,
  'status': _$StatusKunjunganEnumMap[instance.status]!,
  'waktu_datang': instance.waktuDatang.toIso8601String(),
};

const _$StatusKunjunganEnumMap = {
  StatusKunjungan.menunggu: 'menunggu',
  StatusKunjungan.ditangani: 'ditangani',
  StatusKunjungan.selesai: 'selesai',
  StatusKunjungan.$unknown: r'$unknown',
};
