// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

part 'ringkasan_keluarga.g.dart';

/// Desain Gambar 2.23, disesuaikan untuk ICU. Ringkasan riwayat dari keluarga yang divalidasi sebelum disimpan.
///
/// Isinya hanya keterangan keluarga dan wajib diperiksa perawat; "Tidak disebutkan" bila topik itu tidak dibahas.
@JsonSerializable()
class RingkasanKeluarga {
  const RingkasanKeluarga({
    required this.kronologi,
    required this.riwayatPenyakit,
    required this.obatRutin,
    required this.alergi,
    required this.informasiLain,
  });
  
  factory RingkasanKeluarga.fromJson(Map<String, Object?> json) => _$RingkasanKeluargaFromJson(json);
  
  final String kronologi;
  @JsonKey(name: 'riwayat_penyakit')
  final String riwayatPenyakit;
  @JsonKey(name: 'obat_rutin')
  final String obatRutin;
  final String alergi;
  @JsonKey(name: 'informasi_lain')
  final String informasiLain;

  Map<String, Object?> toJson() => _$RingkasanKeluargaToJson(this);
}
