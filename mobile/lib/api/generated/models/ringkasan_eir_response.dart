// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'item_transkrip.dart';
import 'pengisi_eir.dart';
import 'ringkasan_keluarga.dart';
import 'status_sesi_eir.dart';

part 'ringkasan_eir_response.g.dart';

@JsonSerializable()
class RingkasanEirResponse {
  const RingkasanEirResponse({
    required this.idSesi,
    required this.idKunjungan,
    required this.pengisi,
    required this.status,
    required this.waktuPersetujuan,
    required this.waktuSelesai,
    required this.tandaBahaya,
    required this.ringkasan,
    required this.transkrip,
  });
  
  factory RingkasanEirResponse.fromJson(Map<String, Object?> json) => _$RingkasanEirResponseFromJson(json);
  
  @JsonKey(name: 'id_sesi')
  final String idSesi;
  @JsonKey(name: 'id_kunjungan')
  final String idKunjungan;
  final PengisiEir pengisi;
  final StatusSesiEir status;
  @JsonKey(name: 'waktu_persetujuan')
  final DateTime waktuPersetujuan;
  @JsonKey(name: 'waktu_selesai')
  final DateTime? waktuSelesai;

  /// Informasi penting yang ditandai Eir, misalnya alergi obat atau obat pengencer darah.
  @JsonKey(name: 'tanda_bahaya')
  final String? tandaBahaya;

  /// Ringkasan riwayat dari keluarga; wajib diperiksa perawat.
  final RingkasanKeluarga? ringkasan;
  final List<ItemTranskrip> transkrip;

  Map<String, Object?> toJson() => _$RingkasanEirResponseToJson(this);
}
