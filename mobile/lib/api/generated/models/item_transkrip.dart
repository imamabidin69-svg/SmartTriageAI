// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'item_transkrip_peran.dart';

part 'item_transkrip.g.dart';

@JsonSerializable()
class ItemTranskrip {
  const ItemTranskrip({
    required this.peran,
    required this.teks,
    required this.waktu,
  });
  
  factory ItemTranskrip.fromJson(Map<String, Object?> json) => _$ItemTranskripFromJson(json);
  
  final ItemTranskripPeran peran;
  final String teks;
  final DateTime waktu;

  Map<String, Object?> toJson() => _$ItemTranskripToJson(this);
}
