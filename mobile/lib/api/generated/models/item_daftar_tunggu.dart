// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

import 'item_daftar_tunggu_status_tanda.dart';
import 'pasien_triase.dart';
import 'status_kunjungan.dart';
import 'triase_terakhir.dart';

part 'item_daftar_tunggu.g.dart';

/// Satu pasien di papan prioritas ICU. Urutan daftar sudah merupakan urutan prioritas penanganan.
@JsonSerializable()
class ItemDaftarTunggu {
  const ItemDaftarTunggu({
    required this.idKunjungan,
    required this.pasien,
    required this.nomorBed,
    required this.diagnosisMasuk,
    required this.status,
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
  @JsonKey(name: 'nomor_bed')
  final String? nomorBed;
  @JsonKey(name: 'diagnosis_masuk')
  final String? diagnosisMasuk;

  /// menunggu: dirawat; ditangani: sedang tindakan atau operasi.
  final StatusKunjungan status;
  @JsonKey(name: 'waktu_datang')
  final DateTime waktuDatang;
  @JsonKey(name: 'triase_terakhir')
  final TriaseTerakhir? triaseTerakhir;

  /// Menit sejak observasi terakhir, atau sejak masuk bila belum dinilai.
  @JsonKey(name: 'lama_menunggu_menit')
  final int lamaMenungguMenit;

  /// Interval observasi level ini; null bila belum dinilai.
  @JsonKey(name: 'batas_tunggu_menit')
  final int? batasTungguMenit;
  @JsonKey(name: 'status_tanda')
  final ItemDaftarTungguStatusTanda statusTanda;

  /// Ada penilaian awal atau kenaikan level yang belum disetujui dokter.
  @JsonKey(name: 'menunggu_validasi')
  final bool menungguValidasi;
  @JsonKey(name: 'review_diajukan')
  final bool reviewDiajukan;

  /// Keluarga sudah menyelesaikan sesi Eir dan ringkasannya bisa dibaca.
  @JsonKey(name: 'ringkasan_eir_siap')
  final bool ringkasanEirSiap;

  Map<String, Object?> toJson() => _$ItemDaftarTungguToJson(this);
}
