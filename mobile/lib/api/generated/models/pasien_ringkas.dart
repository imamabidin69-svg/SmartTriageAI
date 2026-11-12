// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'jenis_kelamin.dart';

part 'pasien_ringkas.g.dart';

@JsonSerializable()
class PasienRingkas {
  const PasienRingkas({
    required this.idPasien,
    required this.nama,
    required this.jenisKelamin,
    required this.tanggalLahir,
    required this.perkiraanUsia,
    required this.usia,
    required this.nikTersamar,
    required this.idKunjunganAktif,
  });
  
  factory PasienRingkas.fromJson(Map<String, Object?> json) => _$PasienRingkasFromJson(json);
  
  @JsonKey(name: 'id_pasien')
  final String idPasien;
  final String nama;
  @JsonKey(name: 'jenis_kelamin')
  final JenisKelamin jenisKelamin;
  @JsonKey(name: 'tanggal_lahir')
  final DateTime? tanggalLahir;
  @JsonKey(name: 'perkiraan_usia')
  final int? perkiraanUsia;
  final int? usia;

  /// Hanya empat digit terakhir NIK yang ditampilkan.
  @JsonKey(name: 'nik_tersamar')
  final String? nikTersamar;

  /// Masa rawat ICU yang belum selesai, bila ada.
  @JsonKey(name: 'id_kunjungan_aktif')
  final String? idKunjunganAktif;

  Map<String, Object?> toJson() => _$PasienRingkasToJson(this);
}
