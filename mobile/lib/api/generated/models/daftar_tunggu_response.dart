// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'item_daftar_tunggu.dart';

part 'daftar_tunggu_response.g.dart';

@JsonSerializable()
class DaftarTungguResponse {
  const DaftarTungguResponse({
    required this.items,
    required this.waktuServer,
  });
  
  factory DaftarTungguResponse.fromJson(Map<String, Object?> json) => _$DaftarTungguResponseFromJson(json);
  
  final List<ItemDaftarTunggu> items;
  @JsonKey(name: 'waktu_server')
  final DateTime waktuServer;

  Map<String, Object?> toJson() => _$DaftarTungguResponseToJson(this);
}
