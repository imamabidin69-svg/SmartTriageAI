// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'penjelasan_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PenjelasanResponse _$PenjelasanResponseFromJson(Map<String, dynamic> json) =>
    PenjelasanResponse(
      versiModel: json['versi_model'] as String?,
      faktor: (json['faktor'] as List<dynamic>)
          .map((e) => FaktorResponse.fromJson(e as Map<String, dynamic>))
          .toList(),
      probabilitas: (json['probabilitas'] as Map<String, dynamic>?)?.map(
        (k, e) => MapEntry(k, e as num),
      ),
    );

Map<String, dynamic> _$PenjelasanResponseToJson(PenjelasanResponse instance) =>
    <String, dynamic>{
      'versi_model': instance.versiModel,
      'faktor': instance.faktor,
      'probabilitas': instance.probabilitas,
    };
