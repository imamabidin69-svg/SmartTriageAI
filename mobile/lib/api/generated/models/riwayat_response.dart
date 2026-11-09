// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'item_riwayat.dart';
import 'pasien_triase.dart';

part 'riwayat_response.g.dart';

@JsonSerializable()
class RiwayatResponse {
  const RiwayatResponse({
    required this.pasien,
    required this.items,
    required this.kursorBerikutnya,
  });
  
  factory RiwayatResponse.fromJson(Map<String, Object?> json) => _$RiwayatResponseFromJson(json);
  
  final PasienTriase pasien;
  final List<ItemRiwayat> items;

  /// null bila sudah halaman terakhir.
  @JsonKey(name: 'kursor_berikutnya')
  final String? kursorBerikutnya;

  Map<String, Object?> toJson() => _$RiwayatResponseToJson(this);
}
