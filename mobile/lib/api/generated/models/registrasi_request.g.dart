// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'registrasi_request.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

RegistrasiRequest _$RegistrasiRequestFromJson(Map<String, dynamic> json) =>
    RegistrasiRequest(
      idPasien: json['id_pasien'] as String?,
      nama: json['nama'] as String?,
      tanggalLahir: json['tanggal_lahir'] == null
          ? null
          : DateTime.parse(json['tanggal_lahir'] as String),
      perkiraanUsia: (json['perkiraan_usia'] as num?)?.toInt(),
      jenisKelamin: json['jenis_kelamin'] == null
          ? null
          : JenisKelamin.fromJson(json['jenis_kelamin'] as String),
      nik: json['nik'] as String?,
      noTelepon: json['no_telepon'] as String?,
    );

Map<String, dynamic> _$RegistrasiRequestToJson(RegistrasiRequest instance) =>
    <String, dynamic>{
      'id_pasien': instance.idPasien,
      'nama': instance.nama,
      'tanggal_lahir': instance.tanggalLahir?.toIso8601String(),
      'perkiraan_usia': instance.perkiraanUsia,
      'jenis_kelamin': _$JenisKelaminEnumMap[instance.jenisKelamin],
      'nik': instance.nik,
      'no_telepon': instance.noTelepon,
    };

const _$JenisKelaminEnumMap = {
  JenisKelamin.lakiLaki: 'laki_laki',
  JenisKelamin.perempuan: 'perempuan',
  JenisKelamin.$unknown: r'$unknown',
};
