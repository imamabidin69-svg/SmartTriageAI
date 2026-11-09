// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'hasil_pemindaian_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

HasilPemindaianResponse _$HasilPemindaianResponseFromJson(
  Map<String, dynamic> json,
) => HasilPemindaianResponse(
  idPemindaian: json['id_pemindaian'] as String,
  jenisAlat: JenisAlat.fromJson(json['jenis_alat'] as String),
  nilai: json['nilai'] as Map<String, dynamic>,
  keyakinan: Map<String, num?>.from(json['keyakinan'] as Map),
  kolomKosong: (json['kolom_kosong'] as List<dynamic>)
      .map((e) => e as String)
      .toList(),
  pembacaTersedia: json['pembaca_tersedia'] as bool,
);

Map<String, dynamic> _$HasilPemindaianResponseToJson(
  HasilPemindaianResponse instance,
) => <String, dynamic>{
  'id_pemindaian': instance.idPemindaian,
  'jenis_alat': _$JenisAlatEnumMap[instance.jenisAlat]!,
  'nilai': instance.nilai,
  'keyakinan': instance.keyakinan,
  'kolom_kosong': instance.kolomKosong,
  'pembaca_tersedia': instance.pembacaTersedia,
};

const _$JenisAlatEnumMap = {
  JenisAlat.tensimeter: 'tensimeter',
  JenisAlat.oksimeter: 'oksimeter',
  JenisAlat.termometer: 'termometer',
  JenisAlat.bedsideMonitor: 'bedside_monitor',
  JenisAlat.$unknown: r'$unknown',
};
