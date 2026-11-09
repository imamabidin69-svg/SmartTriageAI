// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pengguna_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PenggunaResponse _$PenggunaResponseFromJson(Map<String, dynamic> json) =>
    PenggunaResponse(
      idPengguna: json['id_pengguna'] as String,
      nama: json['nama'] as String,
      email: json['email'] as String,
      peran: Peran.fromJson(json['peran'] as String),
      isActive: json['is_active'] as bool,
    );

Map<String, dynamic> _$PenggunaResponseToJson(PenggunaResponse instance) =>
    <String, dynamic>{
      'id_pengguna': instance.idPengguna,
      'nama': instance.nama,
      'email': instance.email,
      'peran': _$PeranEnumMap[instance.peran]!,
      'is_active': instance.isActive,
    };

const _$PeranEnumMap = {
  Peran.perawat: 'perawat',
  Peran.dokter: 'dokter',
  Peran.admin: 'admin',
  Peran.$unknown: r'$unknown',
};
