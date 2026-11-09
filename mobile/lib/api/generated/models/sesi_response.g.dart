// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'sesi_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

SesiResponse _$SesiResponseFromJson(Map<String, dynamic> json) => SesiResponse(
  pengguna: PenggunaResponse.fromJson(json['pengguna'] as Map<String, dynamic>),
  accessToken: json['access_token'] as String?,
  refreshToken: json['refresh_token'] as String?,
  tokenType: json['token_type'] as String?,
  expiresIn: (json['expires_in'] as num?)?.toInt(),
);

Map<String, dynamic> _$SesiResponseToJson(SesiResponse instance) =>
    <String, dynamic>{
      'pengguna': instance.pengguna,
      'access_token': instance.accessToken,
      'refresh_token': instance.refreshToken,
      'token_type': instance.tokenType,
      'expires_in': instance.expiresIn,
    };
