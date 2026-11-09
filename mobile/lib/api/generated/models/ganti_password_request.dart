// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'ganti_password_request.g.dart';

@JsonSerializable()
class GantiPasswordRequest {
  const GantiPasswordRequest({
    required this.passwordLama,
    required this.passwordBaru,
  });
  
  factory GantiPasswordRequest.fromJson(Map<String, Object?> json) => _$GantiPasswordRequestFromJson(json);
  
  @JsonKey(name: 'password_lama')
  final String passwordLama;
  @JsonKey(name: 'password_baru')
  final String passwordBaru;

  Map<String, Object?> toJson() => _$GantiPasswordRequestToJson(this);
}
