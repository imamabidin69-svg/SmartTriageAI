// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'tautan_eir_response.g.dart';

@JsonSerializable()
class TautanEirResponse {
  const TautanEirResponse({
    required this.token,
    required this.url,
    required this.kedaluwarsa,
  });
  
  factory TautanEirResponse.fromJson(Map<String, Object?> json) => _$TautanEirResponseFromJson(json);
  
  /// Dikirim lewat body POST /eir/sesi.
  final String token;

  /// Alamat halaman Eir untuk kode QR. Token ada di fragmen (#t=), tidak tercatat di log.
  final String url;
  final DateTime kedaluwarsa;

  Map<String, Object?> toJson() => _$TautanEirResponseToJson(this);
}
