// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'tautan_eir_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

TautanEirResponse _$TautanEirResponseFromJson(Map<String, dynamic> json) =>
    TautanEirResponse(
      token: json['token'] as String,
      url: json['url'] as String,
      kedaluwarsa: DateTime.parse(json['kedaluwarsa'] as String),
    );

Map<String, dynamic> _$TautanEirResponseToJson(TautanEirResponse instance) =>
    <String, dynamic>{
      'token': instance.token,
      'url': instance.url,
      'kedaluwarsa': instance.kedaluwarsa.toIso8601String(),
    };
