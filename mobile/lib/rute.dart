/// Alamat halaman dan data yang dibawa saat berpindah halaman.
library;

import 'api/generated/models/pasien_triase.dart';
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

/// Dibawa ke halaman Hasil Penilaian.
class InfoHasil {
  const InfoHasil({this.detail});

  /// Detail yang baru saja diterima, supaya halaman tidak perlu memuat ulang.
  final TriaseDetail? detail;
}

/// Dibawa ke Form Observasi.
class InfoFormTriase {
  const InfoFormTriase({
    required this.pasien,
    this.nomorBed,
    this.waktuDatang,
    this.triaseUlang = false,
    this.ringkasanEirSiap = false,
  });

  final PasienTriase pasien;
  final String? nomorBed;
  final DateTime? waktuDatang;

  /// true untuk observasi berikutnya; false untuk penilaian awal saat pasien baru masuk ICU.
  final bool triaseUlang;
  final bool ringkasanEirSiap;
}
