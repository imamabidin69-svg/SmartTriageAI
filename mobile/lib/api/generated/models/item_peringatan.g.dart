// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'item_peringatan.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ItemPeringatan _$ItemPeringatanFromJson(Map<String, dynamic> json) =>
    ItemPeringatan(
      jenis: ItemPeringatanJenis.fromJson(json['jenis'] as String),
      idKunjungan: json['id_kunjungan'] as String,
      idTriase: json['id_triase'] as String?,
      idSesi: json['id_sesi'] as String?,
      pasien: PasienPeringatan.fromJson(json['pasien'] as Map<String, dynamic>),
      riskLevel: json['risk_level'] == null
          ? null
          : RiskLevel.fromJson(json['risk_level'] as String),
      alasan: json['alasan'] as String,
      waktu: DateTime.parse(json['waktu'] as String),
    );

Map<String, dynamic> _$ItemPeringatanToJson(ItemPeringatan instance) =>
    <String, dynamic>{
      'jenis': _$ItemPeringatanJenisEnumMap[instance.jenis]!,
      'id_kunjungan': instance.idKunjungan,
      'id_triase': instance.idTriase,
      'id_sesi': instance.idSesi,
      'pasien': instance.pasien,
      'risk_level': _$RiskLevelEnumMap[instance.riskLevel],
      'alasan': instance.alasan,
      'waktu': instance.waktu.toIso8601String(),
    };

const _$ItemPeringatanJenisEnumMap = {
  ItemPeringatanJenis.kritisBelumDivalidasi: 'kritis_belum_divalidasi',
  ItemPeringatanJenis.levelNaik: 'level_naik',
  ItemPeringatanJenis.tandaBahayaEir: 'tanda_bahaya_eir',
  ItemPeringatanJenis.$unknown: r'$unknown',
};

const _$RiskLevelEnumMap = {
  RiskLevel.rendah: 'rendah',
  RiskLevel.sedang: 'sedang',
  RiskLevel.tinggi: 'tinggi',
  RiskLevel.kritis: 'kritis',
  RiskLevel.$unknown: r'$unknown',
};
