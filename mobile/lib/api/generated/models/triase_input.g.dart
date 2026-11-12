// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'triase_input.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

TriaseInput _$TriaseInputFromJson(Map<String, dynamic> json) => TriaseInput(
  tingkatKesadaran: TingkatKesadaran.fromJson(
    json['tingkat_kesadaran'] as String,
  ),
  oksigenTambahan: json['oksigen_tambahan'] as bool,
  tandaVital: TandaVital.fromJson(json['tanda_vital'] as Map<String, dynamic>),
  catatan: json['catatan'] as String?,
  ventilator: json['ventilator'] as bool? ?? false,
  vasopresor: json['vasopresor'] as bool? ?? false,
  lab: json['lab'] == null
      ? null
      : HasilLab.fromJson(json['lab'] as Map<String, dynamic>),
  idPemindaian: (json['id_pemindaian'] as List<dynamic>?)
      ?.map((e) => e as String)
      .toList(),
);

Map<String, dynamic> _$TriaseInputToJson(
  TriaseInput instance,
) => <String, dynamic>{
  'tingkat_kesadaran': _$TingkatKesadaranEnumMap[instance.tingkatKesadaran]!,
  'oksigen_tambahan': instance.oksigenTambahan,
  'tanda_vital': instance.tandaVital,
  'lab': instance.lab,
  'ventilator': instance.ventilator,
  'vasopresor': instance.vasopresor,
  'catatan': instance.catatan,
  'id_pemindaian': instance.idPemindaian,
};

const _$TingkatKesadaranEnumMap = {
  TingkatKesadaran.a: 'A',
  TingkatKesadaran.v: 'V',
  TingkatKesadaran.p: 'P',
  TingkatKesadaran.u: 'U',
  TingkatKesadaran.$unknown: r'$unknown',
};
