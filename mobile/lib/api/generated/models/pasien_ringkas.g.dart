// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pasien_ringkas.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PasienRingkas _$PasienRingkasFromJson(Map<String, dynamic> json) =>
    PasienRingkas(
      idPasien: json['id_pasien'] as String,
      nama: json['nama'] as String,
      jenisKelamin: JenisKelamin.fromJson(json['jenis_kelamin'] as String),
      tanggalLahir: json['tanggal_lahir'] == null
          ? null
          : DateTime.parse(json['tanggal_lahir'] as String),
      perkiraanUsia: (json['perkiraan_usia'] as num?)?.toInt(),
      usia: (json['usia'] as num?)?.toInt(),
      nikTersamar: json['nik_tersamar'] as String?,
      idKunjunganAktif: json['id_kunjungan_aktif'] as String?,
    );

Map<String, dynamic> _$PasienRingkasToJson(PasienRingkas instance) =>
    <String, dynamic>{
      'id_pasien': instance.idPasien,
      'nama': instance.nama,
      'jenis_kelamin': _$JenisKelaminEnumMap[instance.jenisKelamin]!,
      'tanggal_lahir': instance.tanggalLahir?.toIso8601String(),
      'perkiraan_usia': instance.perkiraanUsia,
      'usia': instance.usia,
      'nik_tersamar': instance.nikTersamar,
      'id_kunjungan_aktif': instance.idKunjunganAktif,
    };

const _$JenisKelaminEnumMap = {
  JenisKelamin.lakiLaki: 'laki_laki',
  JenisKelamin.perempuan: 'perempuan',
  JenisKelamin.$unknown: r'$unknown',
};
