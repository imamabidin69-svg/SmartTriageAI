// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'penjelasan_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PenjelasanResponse _$PenjelasanResponseFromJson(Map<String, dynamic> json) =>
    PenjelasanResponse(
      versiModel: json['versi_model'] as String?,
      skorNews2: (json['skor_news2'] as num).toInt(),
      levelNews2: RiskLevel.fromJson(json['level_news2'] as String),
      komponenNews2: (json['komponen_news2'] as List<dynamic>)
          .map((e) => FaktorResponse.fromJson(e as Map<String, dynamic>))
          .toList(),
      peluangPerburukan: json['peluang_perburukan'] as num?,
      levelModel: json['level_model'] == null
          ? null
          : RiskLevel.fromJson(json['level_model'] as String),
      faktor: (json['faktor'] as List<dynamic>)
          .map((e) => FaktorResponse.fromJson(e as Map<String, dynamic>))
          .toList(),
    );

Map<String, dynamic> _$PenjelasanResponseToJson(PenjelasanResponse instance) =>
    <String, dynamic>{
      'versi_model': instance.versiModel,
      'skor_news2': instance.skorNews2,
      'level_news2': _$RiskLevelEnumMap[instance.levelNews2]!,
      'komponen_news2': instance.komponenNews2,
      'peluang_perburukan': instance.peluangPerburukan,
      'level_model': _$RiskLevelEnumMap[instance.levelModel],
      'faktor': instance.faktor,
    };

const _$RiskLevelEnumMap = {
  RiskLevel.rendah: 'rendah',
  RiskLevel.sedang: 'sedang',
  RiskLevel.tinggi: 'tinggi',
  RiskLevel.kritis: 'kritis',
  RiskLevel.$unknown: r'$unknown',
};
