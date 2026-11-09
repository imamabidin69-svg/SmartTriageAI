// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'pengguna_response.dart';

part 'sesi_response.g.dart';

/// Respons login dan refresh. Token hanya diisi untuk klien mobile.
@JsonSerializable()
class SesiResponse {
  const SesiResponse({
    required this.pengguna,
    required this.accessToken,
    required this.refreshToken,
    required this.tokenType,
    required this.expiresIn,
  });
  
  factory SesiResponse.fromJson(Map<String, Object?> json) => _$SesiResponseFromJson(json);
  
  final PenggunaResponse pengguna;
  @JsonKey(name: 'access_token')
  final String? accessToken;
  @JsonKey(name: 'refresh_token')
  final String? refreshToken;
  @JsonKey(name: 'token_type')
  final String? tokenType;

  /// Umur access token dalam detik.
  @JsonKey(name: 'expires_in')
  final int? expiresIn;

  Map<String, Object?> toJson() => _$SesiResponseToJson(this);
}
