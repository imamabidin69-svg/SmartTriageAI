import 'package:flutter/material.dart';

import 'api/generated/models/risk_level.dart';

/// Warna mengikuti mockup SKPL Gambar 7.1 dan aplikasi web (Tailwind slate, blue, dan warna level risiko).
abstract final class Warna {
  static const kepala = Color(0xFF1E293B); // slate-800
  static const latar = Color(0xFFF8FAFC); // slate-50
  static const garis = Color(0xFFE2E8F0); // slate-200
  static const teks = Color(0xFF0F172A); // slate-900
  static const teksRedup = Color(0xFF64748B); // slate-500
  static const utama = Color(0xFF2563EB); // blue-600
  static const galat = Color(0xFFB91C1C); // red-700
  static const galatMuda = Color(0xFFFEF2F2); // red-50
  static const peringatan = Color(0xFFB45309); // amber-700
  static const peringatanMuda = Color(0xFFFEF3C7); // amber-100
  static const sukses = Color(0xFF047857); // emerald-700
  static const suksesMuda = Color(0xFFECFDF5); // emerald-50
  static const infoMuda = Color(0xFFEFF6FF); // blue-50

  static const kritis = Color(0xFFB91C1C); // red-700
  static const tinggi = Color(0xFFEA580C); // orange-600
  static const sedang = Color(0xFFD97706); // amber-600
  static const rendah = Color(0xFF059669); // emerald-600

  static Color level(RiskLevel level) => switch (level) {
    RiskLevel.kritis => kritis,
    RiskLevel.tinggi => tinggi,
    RiskLevel.sedang => sedang,
    RiskLevel.rendah || RiskLevel.$unknown => rendah,
  };
}

ThemeData temaAplikasi() {
  final skema = ColorScheme.fromSeed(
    seedColor: Warna.utama,
    primary: Warna.utama,
    error: Warna.galat,
    surface: Colors.white,
  );
  final batas = OutlineInputBorder(
    borderRadius: BorderRadius.circular(10),
    borderSide: const BorderSide(color: Color(0xFFCBD5E1)),
  );
  return ThemeData(
    colorScheme: skema,
    scaffoldBackgroundColor: Warna.latar,
    appBarTheme: const AppBarTheme(
      backgroundColor: Warna.kepala,
      foregroundColor: Colors.white,
      elevation: 0,
      titleTextStyle: TextStyle(fontSize: 20, fontWeight: FontWeight.w700, color: Colors.white),
    ),
    cardTheme: CardThemeData(
      color: Colors.white,
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
        side: const BorderSide(color: Warna.garis),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: Colors.white,
      border: batas,
      enabledBorder: batas,
      focusedBorder: batas.copyWith(borderSide: const BorderSide(color: Warna.utama, width: 2)),
      contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        minimumSize: const Size(48, 52),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        minimumSize: const Size(48, 52),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
      ),
    ),
    snackBarTheme: const SnackBarThemeData(behavior: SnackBarBehavior.floating),
  );
}
