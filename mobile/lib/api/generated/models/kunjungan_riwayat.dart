// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'status_kunjungan.dart';

part 'kunjungan_riwayat.g.dart';

@JsonSerializable()
class KunjunganRiwayat {
  const KunjunganRiwayat({
    required this.idKunjungan,
    required this.waktuDatang,
    required this.waktuDitangani,
    required this.status,
    required this.nomorBed,
    required this.diagnosisMasuk,
  });
  
  factory KunjunganRiwayat.fromJson(Map<String, Object?> json) => _$KunjunganRiwayatFromJson(json);
  
  @JsonKey(name: 'id_kunjungan')
  final String idKunjungan;
  @JsonKey(name: 'waktu_datang')
  final DateTime waktuDatang;
  @JsonKey(name: 'waktu_ditangani')
  final DateTime? waktuDitangani;
  final StatusKunjungan status;
  @JsonKey(name: 'nomor_bed')
  final String? nomorBed;
  @JsonKey(name: 'diagnosis_masuk')
  final String? diagnosisMasuk;

  Map<String, Object?> toJson() => _$KunjunganRiwayatToJson(this);
}
