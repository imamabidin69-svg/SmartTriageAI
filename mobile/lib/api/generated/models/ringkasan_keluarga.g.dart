// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'ringkasan_keluarga.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

RingkasanKeluarga _$RingkasanKeluargaFromJson(Map<String, dynamic> json) =>
    RingkasanKeluarga(
      kronologi: json['kronologi'] as String,
      riwayatPenyakit: json['riwayat_penyakit'] as String,
      obatRutin: json['obat_rutin'] as String,
      alergi: json['alergi'] as String,
      informasiLain: json['informasi_lain'] as String,
    );

Map<String, dynamic> _$RingkasanKeluargaToJson(RingkasanKeluarga instance) =>
    <String, dynamic>{
      'kronologi': instance.kronologi,
      'riwayat_penyakit': instance.riwayatPenyakit,
      'obat_rutin': instance.obatRutin,
      'alergi': instance.alergi,
      'informasi_lain': instance.informasiLain,
    };
