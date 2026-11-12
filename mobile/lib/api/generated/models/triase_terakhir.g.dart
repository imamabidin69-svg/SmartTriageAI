// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'triase_terakhir.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

TriaseTerakhir _$TriaseTerakhirFromJson(Map<String, dynamic> json) =>
    TriaseTerakhir(
      idTriase: json['id_triase'] as String,
      jenis: JenisTriase.fromJson(json['jenis'] as String),
      riskLevel: RiskLevel.fromJson(json['risk_level'] as String),
      statusValidasi: StatusValidasi.fromJson(
        json['status_validasi'] as String,
      ),
      skorNews2: (json['skor_news2'] as num).toInt(),
      peluangPerburukan: json['peluang_perburukan'] as num?,
      waktuTriase: DateTime.parse(json['waktu_triase'] as String),
    );

Map<String, dynamic> _$TriaseTerakhirToJson(TriaseTerakhir instance) =>
    <String, dynamic>{
      'id_triase': instance.idTriase,
      'jenis': _$JenisTriaseEnumMap[instance.jenis]!,
      'risk_level': _$RiskLevelEnumMap[instance.riskLevel]!,
      'status_validasi': _$StatusValidasiEnumMap[instance.statusValidasi]!,
      'skor_news2': instance.skorNews2,
      'peluang_perburukan': instance.peluangPerburukan,
      'waktu_triase': instance.waktuTriase.toIso8601String(),
    };

const _$JenisTriaseEnumMap = {
  JenisTriase.awal: 'awal',
  JenisTriase.ulang: 'ulang',
  JenisTriase.$unknown: r'$unknown',
};

const _$RiskLevelEnumMap = {
  RiskLevel.rendah: 'rendah',
  RiskLevel.sedang: 'sedang',
  RiskLevel.tinggi: 'tinggi',
  RiskLevel.kritis: 'kritis',
  RiskLevel.$unknown: r'$unknown',
};

const _$StatusValidasiEnumMap = {
  StatusValidasi.menunggu: 'menunggu',
  StatusValidasi.disetujui: 'disetujui',
  StatusValidasi.menungguReviewDokter: 'menunggu_review_dokter',
  StatusValidasi.dikoreksi: 'dikoreksi',
  StatusValidasi.tercatat: 'tercatat',
  StatusValidasi.$unknown: r'$unknown',
};
