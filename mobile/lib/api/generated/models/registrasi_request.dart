// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'jenis_kelamin.dart';

part 'registrasi_request.g.dart';

/// Registrasi singkat (Desain Gambar 2.5).
///
/// Bila id_pasien diisi, pasien lama dipakai dan isian identitas lain diabaikan tanpa divalidasi.
/// (keputusan K8), karena form bisa saja masih membawa isian dari pencarian sebelumnya. Bila tidak,.
/// nama, jenis kelamin, dan tanggal lahir atau perkiraan usia wajib diisi; pemeriksaan ini dilakukan.
/// KunjunganService supaya pesannya tetap per field.
@JsonSerializable()
class RegistrasiRequest {
  const RegistrasiRequest({
    required this.idPasien,
    required this.nama,
    required this.tanggalLahir,
    required this.perkiraanUsia,
    required this.jenisKelamin,
    required this.nik,
    required this.noTelepon,
  });
  
  factory RegistrasiRequest.fromJson(Map<String, Object?> json) => _$RegistrasiRequestFromJson(json);
  
  @JsonKey(name: 'id_pasien')
  final String? idPasien;
  final String? nama;
  @JsonKey(name: 'tanggal_lahir')
  final DateTime? tanggalLahir;
  @JsonKey(name: 'perkiraan_usia')
  final int? perkiraanUsia;
  @JsonKey(name: 'jenis_kelamin')
  final JenisKelamin? jenisKelamin;
  final String? nik;
  @JsonKey(name: 'no_telepon')
  final String? noTelepon;

  Map<String, Object?> toJson() => _$RegistrasiRequestToJson(this);
}
