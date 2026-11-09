// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pasien_triase.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PasienTriase _$PasienTriaseFromJson(Map<String, dynamic> json) => PasienTriase(
  idPasien: json['id_pasien'] as String,
  nama: json['nama'] as String,
  usia: (json['usia'] as num?)?.toInt(),
  jenisKelamin: JenisKelamin.fromJson(json['jenis_kelamin'] as String),
);

Map<String, dynamic> _$PasienTriaseToJson(PasienTriase instance) =>
    <String, dynamic>{
      'id_pasien': instance.idPasien,
      'nama': instance.nama,
      'usia': instance.usia,
      'jenis_kelamin': _$JenisKelaminEnumMap[instance.jenisKelamin]!,
    };

const _$JenisKelaminEnumMap = {
  JenisKelamin.lakiLaki: 'laki_laki',
  JenisKelamin.perempuan: 'perempuan',
  JenisKelamin.$unknown: r'$unknown',
};
