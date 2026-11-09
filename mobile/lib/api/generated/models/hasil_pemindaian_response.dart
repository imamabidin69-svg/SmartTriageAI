// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'jenis_alat.dart';

part 'hasil_pemindaian_response.g.dart';

@JsonSerializable()
class HasilPemindaianResponse {
  const HasilPemindaianResponse({
    required this.idPemindaian,
    required this.jenisAlat,
    required this.nilai,
    required this.keyakinan,
    required this.kolomKosong,
    required this.pembacaTersedia,
  });
  
  factory HasilPemindaianResponse.fromJson(Map<String, Object?> json) => _$HasilPemindaianResponseFromJson(json);
  
  /// Dikirim lewat field id_pemindaian di form triase.
  @JsonKey(name: 'id_pemindaian')
  final String idPemindaian;
  @JsonKey(name: 'jenis_alat')
  final JenisAlat jenisAlat;

  /// Nilai per kolom tanda vital. null berarti kolom dibiarkan kosong untuk diisi manual.
  final Map<String, dynamic> nilai;

  /// Keyakinan model per kolom, null bila tidak terbaca.
  final Map<String, num?> keyakinan;
  @JsonKey(name: 'kolom_kosong')
  final List<String> kolomKosong;

  /// false bila model pembaca layar belum dimuat; semua kolom kosong.
  @JsonKey(name: 'pembaca_tersedia')
  final bool pembacaTersedia;

  Map<String, Object?> toJson() => _$HasilPemindaianResponseToJson(this);
}
