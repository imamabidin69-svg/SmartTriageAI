// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'validasi_request.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ValidasiRequest _$ValidasiRequestFromJson(Map<String, dynamic> json) =>
    ValidasiRequest(
      aksi: ValidasiRequestAksi.fromJson(json['aksi'] as String),
      riskLevel: json['risk_level'] == null
          ? null
          : RiskLevel.fromJson(json['risk_level'] as String),
      alasan: json['alasan'] as String?,
    );

Map<String, dynamic> _$ValidasiRequestToJson(ValidasiRequest instance) =>
    <String, dynamic>{
      'aksi': _$ValidasiRequestAksiEnumMap[instance.aksi]!,
      'risk_level': _$RiskLevelEnumMap[instance.riskLevel],
      'alasan': instance.alasan,
    };

const _$ValidasiRequestAksiEnumMap = {
  ValidasiRequestAksi.setujui: 'setujui',
  ValidasiRequestAksi.koreksi: 'koreksi',
  ValidasiRequestAksi.ajukanReview: 'ajukan_review',
  ValidasiRequestAksi.$unknown: r'$unknown',
};

const _$RiskLevelEnumMap = {
  RiskLevel.rendah: 'rendah',
  RiskLevel.sedang: 'sedang',
  RiskLevel.tinggi: 'tinggi',
  RiskLevel.kritis: 'kritis',
  RiskLevel.$unknown: r'$unknown',
};
