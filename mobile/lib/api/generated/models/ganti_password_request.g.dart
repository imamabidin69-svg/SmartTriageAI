// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'ganti_password_request.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

GantiPasswordRequest _$GantiPasswordRequestFromJson(
  Map<String, dynamic> json,
) => GantiPasswordRequest(
  passwordLama: json['password_lama'] as String,
  passwordBaru: json['password_baru'] as String,
);

Map<String, dynamic> _$GantiPasswordRequestToJson(
  GantiPasswordRequest instance,
) => <String, dynamic>{
  'password_lama': instance.passwordLama,
  'password_baru': instance.passwordBaru,
};
