// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'hasil_lab.dart';
import 'tanda_vital.dart';
import 'tingkat_kesadaran.dart';

part 'triase_input.g.dart';

/// Observasi pasien ICU. Tanda vital, kesadaran, dan oksigen wajib karena dipakai NEWS2; sisanya opsional.
@JsonSerializable()
class TriaseInput {
  const TriaseInput({
    required this.tingkatKesadaran,
    required this.oksigenTambahan,
    required this.tandaVital,
    required this.catatan,
    this.ventilator = false,
    this.vasopresor = false,
    this.lab,
    this.idPemindaian,
  });
  
  factory TriaseInput.fromJson(Map<String, Object?> json) => _$TriaseInputFromJson(json);
  
  /// AVPU: A sadar penuh, V suara, P nyeri, U tidak respons.
  @JsonKey(name: 'tingkat_kesadaran')
  final TingkatKesadaran tingkatKesadaran;

  /// true bila pasien mendapat oksigen tambahan (nasal, masker, ventilator).
  @JsonKey(name: 'oksigen_tambahan')
  final bool oksigenTambahan;
  @JsonKey(name: 'tanda_vital')
  final TandaVital tandaVital;
  final HasilLab? lab;
  final bool ventilator;
  final bool vasopresor;
  final String? catatan;

  /// Hasil POST /pemindaian yang nilainya dipakai di form ini.
  @JsonKey(name: 'id_pemindaian')
  final List<String>? idPemindaian;

  Map<String, Object?> toJson() => _$TriaseInputToJson(this);
}
