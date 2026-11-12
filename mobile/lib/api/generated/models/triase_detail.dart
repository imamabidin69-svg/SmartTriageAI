// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'hasil_lab_response.dart';
import 'jenis_triase.dart';
import 'pasien_triase.dart';
import 'pengguna_ringkas.dart';
import 'penjelasan_response.dart';
import 'peringatan.dart';
import 'risk_level.dart';
import 'status_kunjungan.dart';
import 'status_validasi.dart';
import 'sumber_rekomendasi.dart';
import 'sumber_tanda_vital.dart';
import 'tanda_vital_response.dart';
import 'tingkat_kesadaran.dart';

part 'triase_detail.g.dart';

/// Bentuk yang sama dipakai respons POST /kunjungan/{id}/triase dan GET /triase/{id}.
@JsonSerializable()
class TriaseDetail {
  const TriaseDetail({
    required this.idTriase,
    required this.idKunjungan,
    required this.jenis,
    required this.pasien,
    required this.nomorBed,
    required this.statusKunjungan,
    required this.tingkatKesadaran,
    required this.oksigenTambahan,
    required this.tandaVital,
    required this.lab,
    required this.ventilator,
    required this.vasopresor,
    required this.catatan,
    required this.sumberTandaVital,
    required this.skorNews2,
    required this.peluangPerburukan,
    required this.levelSebelumnya,
    required this.riskLevel,
    required this.sumberRekomendasi,
    required this.penjelasanAi,
    required this.statusValidasi,
    required this.dibuatOleh,
    required this.divalidasiOleh,
    required this.waktuTriase,
    required this.peringatan,
    required this.catatanValidasiTerakhir,
  });
  
  factory TriaseDetail.fromJson(Map<String, Object?> json) => _$TriaseDetailFromJson(json);
  
  @JsonKey(name: 'id_triase')
  final String idTriase;
  @JsonKey(name: 'id_kunjungan')
  final String idKunjungan;
  final JenisTriase jenis;
  final PasienTriase pasien;
  @JsonKey(name: 'nomor_bed')
  final String? nomorBed;

  /// Status pasien saat ini: dirawat, sedang tindakan, keluar.
  @JsonKey(name: 'status_kunjungan')
  final StatusKunjungan statusKunjungan;
  @JsonKey(name: 'tingkat_kesadaran')
  final TingkatKesadaran tingkatKesadaran;
  @JsonKey(name: 'oksigen_tambahan')
  final bool oksigenTambahan;
  @JsonKey(name: 'tanda_vital')
  final TandaVitalResponse tandaVital;
  final HasilLabResponse lab;
  final bool ventilator;
  final bool vasopresor;
  final String? catatan;
  @JsonKey(name: 'sumber_tanda_vital')
  final SumberTandaVital sumberTandaVital;
  @JsonKey(name: 'skor_news2')
  final int skorNews2;
  @JsonKey(name: 'peluang_perburukan')
  final num? peluangPerburukan;

  /// Level observasi sebelumnya di masa rawat yang sama.
  @JsonKey(name: 'level_sebelumnya')
  final RiskLevel? levelSebelumnya;
  @JsonKey(name: 'risk_level')
  final RiskLevel riskLevel;
  @JsonKey(name: 'sumber_rekomendasi')
  final SumberRekomendasi sumberRekomendasi;
  @JsonKey(name: 'penjelasan_ai')
  final PenjelasanResponse penjelasanAi;
  @JsonKey(name: 'status_validasi')
  final StatusValidasi statusValidasi;
  @JsonKey(name: 'dibuat_oleh')
  final PenggunaRingkas dibuatOleh;
  @JsonKey(name: 'divalidasi_oleh')
  final PenggunaRingkas? divalidasiOleh;
  @JsonKey(name: 'waktu_triase')
  final DateTime waktuTriase;
  final List<Peringatan> peringatan;

  /// Alasan koreksi atau ajuan review terakhir, bila ada.
  @JsonKey(name: 'catatan_validasi_terakhir')
  final String? catatanValidasiTerakhir;

  Map<String, Object?> toJson() => _$TriaseDetailToJson(this);
}
