// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'kategori_keluhan.dart';
import 'tanda_vital.dart';
import 'tingkat_kesadaran.dart';

part 'triase_input.g.dart';

/// Isian form triase (Desain Gambar 2.8). Kategori keluhan dan skala nyeri wajib (keputusan K3).
@JsonSerializable()
class TriaseInput {
  const TriaseInput({
    required this.keluhanUtama,
    required this.gejala,
    required this.kategoriKeluhan,
    required this.skalaNyeri,
    required this.tingkatKesadaran,
    required this.tandaVital,
    this.idPemindaian,
  });
  
  factory TriaseInput.fromJson(Map<String, Object?> json) => _$TriaseInputFromJson(json);
  
  @JsonKey(name: 'keluhan_utama')
  final String keluhanUtama;
  final String gejala;
  @JsonKey(name: 'kategori_keluhan')
  final KategoriKeluhan kategoriKeluhan;
  @JsonKey(name: 'skala_nyeri')
  final int skalaNyeri;

  /// AVPU: A sadar penuh, V suara, P nyeri, U tidak respons.
  @JsonKey(name: 'tingkat_kesadaran')
  final TingkatKesadaran tingkatKesadaran;
  @JsonKey(name: 'tanda_vital')
  final TandaVital tandaVital;

  /// Hasil POST /pemindaian yang nilainya dipakai di form ini.
  @JsonKey(name: 'id_pemindaian')
  final List<String>? idPemindaian;

  Map<String, Object?> toJson() => _$TriaseInputToJson(this);
}
