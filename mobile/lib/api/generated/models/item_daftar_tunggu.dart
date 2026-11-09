// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'item_daftar_tunggu_status_tanda.dart';
import 'pasien_triase.dart';
import 'triase_terakhir.dart';

part 'item_daftar_tunggu.g.dart';

@JsonSerializable()
class ItemDaftarTunggu {
  const ItemDaftarTunggu({
    required this.idKunjungan,
    required this.pasien,
    required this.waktuDatang,
    required this.triaseTerakhir,
    required this.lamaMenungguMenit,
    required this.batasTungguMenit,
    required this.statusTanda,
    required this.menungguValidasi,
    required this.reviewDiajukan,
    required this.ringkasanEirSiap,
  });
  
  factory ItemDaftarTunggu.fromJson(Map<String, Object?> json) => _$ItemDaftarTungguFromJson(json);
  
  @JsonKey(name: 'id_kunjungan')
  final String idKunjungan;
  final PasienTriase pasien;
  @JsonKey(name: 'waktu_datang')
  final DateTime waktuDatang;
  @JsonKey(name: 'triase_terakhir')
  final TriaseTerakhir? triaseTerakhir;

  /// Sejak triase terakhir, atau sejak datang bila belum ditriase.
  @JsonKey(name: 'lama_menunggu_menit')
  final int lamaMenungguMenit;

  /// Batas dari konfigurasi; null untuk kritis dan belum ditriase.
  @JsonKey(name: 'batas_tunggu_menit')
  final int? batasTungguMenit;
  @JsonKey(name: 'status_tanda')
  final ItemDaftarTungguStatusTanda statusTanda;
  @JsonKey(name: 'menunggu_validasi')
  final bool menungguValidasi;
  @JsonKey(name: 'review_diajukan')
  final bool reviewDiajukan;

  /// Sesi Eir terakhir selesai dengan ringkasan yang belum dipakai untuk triase berikutnya.
  @JsonKey(name: 'ringkasan_eir_siap')
  final bool ringkasanEirSiap;

  Map<String, Object?> toJson() => _$ItemDaftarTungguToJson(this);
}
