// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'kategori_keluhan.dart';

part 'ringkasan_triase.g.dart';

/// Desain Gambar 2.23. Ringkasan dari LLM yang divalidasi sebelum menjadi draf form triase.
@JsonSerializable()
class RingkasanTriase {
  const RingkasanTriase({
    required this.keluhanUtama,
    required this.gejala,
    required this.onset,
    required this.kategoriKeluhan,
  });
  
  factory RingkasanTriase.fromJson(Map<String, Object?> json) => _$RingkasanTriaseFromJson(json);
  
  @JsonKey(name: 'keluhan_utama')
  final String keluhanUtama;
  final String gejala;
  final String onset;
  @JsonKey(name: 'kategori_keluhan')
  final KategoriKeluhan kategoriKeluhan;

  Map<String, Object?> toJson() => _$RingkasanTriaseToJson(this);
}
