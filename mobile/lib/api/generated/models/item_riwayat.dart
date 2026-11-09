// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'jenis_triase.dart';
import 'kategori_keluhan.dart';
import 'kunjungan_riwayat.dart';
import 'pengguna_ringkas.dart';
import 'risk_level.dart';
import 'status_validasi.dart';
import 'sumber_rekomendasi.dart';
import 'tanda_vital_response.dart';

part 'item_riwayat.g.dart';

@JsonSerializable()
class ItemRiwayat {
  const ItemRiwayat({
    required this.idTriase,
    required this.jenis,
    required this.waktuTriase,
    required this.keluhanUtama,
    required this.kategoriKeluhan,
    required this.riskLevel,
    required this.sumberRekomendasi,
    required this.statusValidasi,
    required this.tandaVital,
    required this.dibuatOleh,
    required this.divalidasiOleh,
    required this.kunjungan,
  });
  
  factory ItemRiwayat.fromJson(Map<String, Object?> json) => _$ItemRiwayatFromJson(json);
  
  @JsonKey(name: 'id_triase')
  final String idTriase;
  final JenisTriase jenis;
  @JsonKey(name: 'waktu_triase')
  final DateTime waktuTriase;
  @JsonKey(name: 'keluhan_utama')
  final String keluhanUtama;
  @JsonKey(name: 'kategori_keluhan')
  final KategoriKeluhan? kategoriKeluhan;
  @JsonKey(name: 'risk_level')
  final RiskLevel riskLevel;
  @JsonKey(name: 'sumber_rekomendasi')
  final SumberRekomendasi sumberRekomendasi;
  @JsonKey(name: 'status_validasi')
  final StatusValidasi statusValidasi;
  @JsonKey(name: 'tanda_vital')
  final TandaVitalResponse tandaVital;
  @JsonKey(name: 'dibuat_oleh')
  final PenggunaRingkas dibuatOleh;
  @JsonKey(name: 'divalidasi_oleh')
  final PenggunaRingkas? divalidasiOleh;
  final KunjunganRiwayat kunjungan;

  Map<String, Object?> toJson() => _$ItemRiwayatToJson(this);
}
