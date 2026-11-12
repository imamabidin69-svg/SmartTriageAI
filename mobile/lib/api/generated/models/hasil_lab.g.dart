// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'hasil_lab.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

HasilLab _$HasilLabFromJson(Map<String, dynamic> json) => HasilLab(
  laktat: json['laktat'],
  kreatinin: json['kreatinin'],
  trombosit: (json['trombosit'] as num?)?.toInt(),
  leukosit: json['leukosit'],
  bilirubin: json['bilirubin'],
);

Map<String, dynamic> _$HasilLabToJson(HasilLab instance) => <String, dynamic>{
  'laktat': instance.laktat,
  'kreatinin': instance.kreatinin,
  'trombosit': instance.trombosit,
  'leukosit': instance.leukosit,
  'bilirubin': instance.bilirubin,
};
