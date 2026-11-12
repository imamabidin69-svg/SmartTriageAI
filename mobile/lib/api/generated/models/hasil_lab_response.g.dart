// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'hasil_lab_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

HasilLabResponse _$HasilLabResponseFromJson(Map<String, dynamic> json) =>
    HasilLabResponse(
      laktat: json['laktat'] as num?,
      kreatinin: json['kreatinin'] as num?,
      trombosit: (json['trombosit'] as num?)?.toInt(),
      leukosit: json['leukosit'] as num?,
      bilirubin: json['bilirubin'] as num?,
    );

Map<String, dynamic> _$HasilLabResponseToJson(HasilLabResponse instance) =>
    <String, dynamic>{
      'laktat': instance.laktat,
      'kreatinin': instance.kreatinin,
      'trombosit': instance.trombosit,
      'leukosit': instance.leukosit,
      'bilirubin': instance.bilirubin,
    };
