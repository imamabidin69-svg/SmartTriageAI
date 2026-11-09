// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'item_peringatan.dart';

part 'daftar_peringatan_response.g.dart';

@JsonSerializable()
class DaftarPeringatanResponse {
  const DaftarPeringatanResponse({
    required this.items,
  });
  
  factory DaftarPeringatanResponse.fromJson(Map<String, Object?> json) => _$DaftarPeringatanResponseFromJson(json);
  
  final List<ItemPeringatan> items;

  Map<String, Object?> toJson() => _$DaftarPeringatanResponseToJson(this);
}
