/// Alamat halaman dan data yang dibawa saat berpindah halaman.
library;

import 'api/generated/models/pasien_triase.dart';
import 'api/generated/models/status_kunjungan.dart';
import 'api/generated/models/triase_detail.dart';

abstract final class Rute {
  static const mulai = '/mulai';
  static const masuk = '/masuk';
  static const antrean = '/antrean';
  static const triaseBaru = '/triase-baru';
  static const riwayat = '/riwayat';
  static const profil = '/profil';
  static const pemindaian = '/pemindaian';

  static String hasil(String idTriase) => '/triase/$idTriase';
  static String formTriase(String idKunjungan) => '/kunjungan/$idKunjungan/triase';
  static String kodeQrEir(String idKunjungan) => '/kunjungan/$idKunjungan/kode-eir';
  static String ringkasanEir(String idKunjungan) => '/kunjungan/$idKunjungan/ringkasan-eir';
  static String riwayatPasien(String idPasien) => '/pasien/$idPasien/riwayat';
}

/// Dibawa ke halaman Hasil dan Penjelasan.
class InfoHasil {
  const InfoHasil({this.detail, this.statusKunjungan});

  /// Detail yang baru saja diterima, supaya halaman tidak perlu memuat ulang.
  final TriaseDetail? detail;

  /// Status kunjungan saat halaman dibuka. Tombol status kunjungan untuk dokter hanya muncul bila diketahui.
  final StatusKunjungan? statusKunjungan;
}

/// Dibawa ke Form Triase.
class InfoFormTriase {
  const InfoFormTriase({
    required this.pasien,
    this.waktuDatang,
    this.triaseUlang = false,
    this.ringkasanEirSiap = false,
  });

  final PasienTriase pasien;
  final DateTime? waktuDatang;
  final bool triaseUlang;
  final bool ringkasanEirSiap;
}
