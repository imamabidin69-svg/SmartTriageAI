import 'package:flutter/material.dart';

import 'api/generated/models/risk_level.dart';

/// Warna mengikuti panduan gaya tahap 6D. Biru tua diambil dari perisai di logo. Merah, oranye, kuning, dan hijau
/// hanya dipakai untuk level risiko (urutan Manchester Triage System), elemen lain memakai warna netral.
abstract final class Warna {
  static const kepala = Color(0xFF0F2A4F); // biru tua: header dan pilihan aktif
  static const kepalaTeks2 = Color(0xFFB9C7DA); // teks kedua di atas header
  static const utama = Color(0xFF1C58B0); // tombol utama dan tautan, kontras 6,8:1
  static const utamaGaris = Color(0xFF5D84C2);
  static const utamaMuda = Color(0xFFF1F6FD); // latar isian yang terisi dari pemindaian
  static const latar = Color(0xFFF2F4F6);
  static const garis = Color(0xFFD3DAE1);
  static const garisLembut = Color(0xFFE6EAEE);
  static const garisIsian = Color(0xFF7D8896); // batas kotak isian, kontras 3,6:1
  static const teks = Color(0xFF18212C);
  static const teksRedup = Color(0xFF4B5765);
  static const teksSamar = Color(0xFF5F6B79);
  static const nol = Color(0xFFA3ACB7); // angka nol di ringkasan level
  static const galat = Color(0xFFB42318);
  static const waspada = Color(0xFF8A4B00); // teks perhatian, misalnya perlu triase ulang
  static const waspadaGaris = Color(0xFFE0A100);

  static const kritis = Color(0xFFC62828);
  static const tinggi = Color(0xFFE8590C);
  static const sedang = Color(0xFFE0A100);
  static const rendah = Color(0xFF2F8F4E);
  static const belum = Color(0xFF8C97A4); // belum ditriase, tanpa warna level

  static Color level(RiskLevel level) => switch (level) {
    RiskLevel.kritis => kritis,
    RiskLevel.tinggi => tinggi,
    RiskLevel.sedang => sedang,
    RiskLevel.rendah || RiskLevel.$unknown => rendah,
  };
}

/// Atkinson Hyperlegible Next, dideklarasikan di pubspec.yaml.
const hurufAplikasi = 'AtkinsonHyperlegibleNext';

/// Angka rata (tabular) supaya jam, lama tunggu, dan tanda vital sejajar saat dibaca cepat.
const angkaRata = [FontFeature.tabularFigures()];

/// Gaya teks untuk tema. fontFamily ditulis eksplisit karena gaya di tema komponen (AppBar, tombol, snackbar)
/// tidak mewarisi huruf dari textTheme; tanpa ini judul dan tombol jatuh ke huruf bawaan perangkat.
TextStyle _gaya(double ukuran, FontWeight tebal, {Color warna = Warna.teks, double? tinggi}) => TextStyle(
  fontFamily: hurufAplikasi,
  fontSize: ukuran,
  fontWeight: tebal,
  color: warna,
  height: tinggi,
  fontFeatures: angkaRata,
);

ThemeData temaAplikasi() {
  final skema = ColorScheme.fromSeed(seedColor: Warna.utama).copyWith(
    primary: Warna.utama,
    onPrimary: Colors.white,
    secondary: Warna.kepala,
    onSecondary: Colors.white,
    error: Warna.galat,
    surface: Colors.white,
    onSurface: Warna.teks,
    onSurfaceVariant: Warna.teksRedup,
    outline: Warna.garisIsian,
    outlineVariant: Warna.garis,
    surfaceTint: Colors.transparent,
    surfaceContainerLowest: Colors.white,
    surfaceContainerLow: Colors.white,
    surfaceContainer: Colors.white,
    surfaceContainerHigh: Colors.white,
    surfaceContainerHighest: Warna.latar,
  );
  final teks = TextTheme(
    headlineSmall: _gaya(24, FontWeight.w700),
    titleLarge: _gaya(20, FontWeight.w700),
    titleMedium: _gaya(17, FontWeight.w700),
    titleSmall: _gaya(15, FontWeight.w700),
    bodyLarge: _gaya(16, FontWeight.w400),
    bodyMedium: _gaya(15, FontWeight.w400, tinggi: 1.35),
    bodySmall: _gaya(13, FontWeight.w400, warna: Warna.teksRedup),
    labelLarge: _gaya(15, FontWeight.w700),
    labelMedium: _gaya(13, FontWeight.w600),
    labelSmall: _gaya(12, FontWeight.w600),
  );
  final sudut = RoundedRectangleBorder(borderRadius: BorderRadius.circular(6));
  OutlineInputBorder batas(Color warna, [double tebal = 1]) => OutlineInputBorder(
    borderRadius: BorderRadius.circular(6),
    borderSide: BorderSide(color: warna, width: tebal),
  );
  const tombol = Size(48, 48);
  final teksTombol = _gaya(16, FontWeight.w700);

  return ThemeData(
    colorScheme: skema,
    fontFamily: hurufAplikasi,
    textTheme: teks,
    scaffoldBackgroundColor: Warna.latar,
    canvasColor: Colors.white,
    dividerTheme: const DividerThemeData(color: Warna.garis, space: 1, thickness: 1),
    appBarTheme: AppBarTheme(
      backgroundColor: Warna.kepala,
      foregroundColor: Colors.white,
      elevation: 0,
      scrolledUnderElevation: 0,
      titleSpacing: 16,
      titleTextStyle: _gaya(20, FontWeight.w700, warna: Colors.white),
    ),
    cardTheme: CardThemeData(
      color: Colors.white,
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: const BorderSide(color: Warna.garis),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: Colors.white,
      // Label selalu tampil di atas isian supaya tetap terbaca setelah kotak terisi.
      floatingLabelBehavior: FloatingLabelBehavior.always,
      floatingLabelStyle: WidgetStateTextStyle.resolveWith(
        (state) => _gaya(
          15,
          FontWeight.w700,
          warna: state.contains(WidgetState.error)
              ? Warna.galat
              : state.contains(WidgetState.focused)
              ? Warna.utama
              : Warna.teks,
        ),
      ),
      labelStyle: _gaya(15, FontWeight.w600, warna: Warna.teksRedup),
      hintStyle: _gaya(15, FontWeight.w400, warna: Warna.teksSamar),
      helperStyle: _gaya(13, FontWeight.w400, warna: Warna.teksSamar),
      errorStyle: _gaya(13, FontWeight.w600, warna: Warna.galat),
      suffixStyle: _gaya(14, FontWeight.w400, warna: Warna.teksSamar),
      suffixIconColor: Warna.teksSamar,
      border: batas(Warna.garisIsian),
      enabledBorder: batas(Warna.garisIsian),
      disabledBorder: batas(Warna.garis),
      focusedBorder: batas(Warna.utama, 2),
      errorBorder: batas(Warna.galat, 1.5),
      focusedErrorBorder: batas(Warna.galat, 2),
      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: Warna.utama,
        foregroundColor: Colors.white,
        disabledBackgroundColor: Warna.garis,
        disabledForegroundColor: Warna.teksSamar,
        minimumSize: tombol,
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
        shape: sudut,
        textStyle: teksTombol,
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style:
          OutlinedButton.styleFrom(
            foregroundColor: Warna.utama,
            disabledForegroundColor: Warna.teksSamar,
            minimumSize: tombol,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            shape: sudut,
            textStyle: teksTombol,
          ).copyWith(
            side: WidgetStateProperty.resolveWith(
              (state) => BorderSide(color: state.contains(WidgetState.disabled) ? Warna.garis : Warna.utamaGaris),
            ),
          ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: Warna.utama,
        minimumSize: tombol,
        padding: const EdgeInsets.symmetric(horizontal: 12),
        shape: sudut,
        textStyle: _gaya(15, FontWeight.w700),
      ),
    ),
    segmentedButtonTheme: SegmentedButtonThemeData(
      style: ButtonStyle(
        minimumSize: const WidgetStatePropertyAll(tombol),
        shape: WidgetStatePropertyAll(sudut),
        side: const WidgetStatePropertyAll(BorderSide(color: Warna.garisIsian)),
        textStyle: WidgetStatePropertyAll(_gaya(16, FontWeight.w700)),
        backgroundColor: WidgetStateProperty.resolveWith(
          (state) => state.contains(WidgetState.selected) ? Warna.kepala : Colors.white,
        ),
        foregroundColor: WidgetStateProperty.resolveWith(
          (state) => state.contains(WidgetState.selected) ? Colors.white : Warna.teks,
        ),
      ),
    ),
    chipTheme: ChipThemeData(
      backgroundColor: Colors.white,
      selectedColor: Warna.kepala,
      disabledColor: Warna.latar,
      showCheckmark: false,
      side: const BorderSide(color: Warna.garisIsian),
      shape: sudut,
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 8),
      labelStyle: WidgetStateTextStyle.resolveWith(
        (state) => _gaya(15, FontWeight.w700, warna: state.contains(WidgetState.selected) ? Colors.white : Warna.teks),
      ),
    ),
    dialogTheme: DialogThemeData(
      backgroundColor: Colors.white,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      titleTextStyle: _gaya(20, FontWeight.w700),
      contentTextStyle: _gaya(15, FontWeight.w400, tinggi: 1.4),
    ),
    bottomSheetTheme: const BottomSheetThemeData(
      backgroundColor: Colors.white,
      dragHandleColor: Warna.garis,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(12))),
    ),
    listTileTheme: ListTileThemeData(
      iconColor: Warna.teksSamar,
      titleTextStyle: _gaya(16, FontWeight.w600),
      subtitleTextStyle: _gaya(14, FontWeight.w400, warna: Warna.teksRedup),
    ),
    snackBarTheme: SnackBarThemeData(
      behavior: SnackBarBehavior.floating,
      backgroundColor: Warna.teks,
      contentTextStyle: _gaya(15, FontWeight.w400, warna: Colors.white),
      actionTextColor: const Color(0xFFB9D3FF),
      shape: sudut,
    ),
    badgeTheme: const BadgeThemeData(backgroundColor: Warna.kritis, textColor: Colors.white),
    progressIndicatorTheme: const ProgressIndicatorThemeData(color: Warna.utama),
    radioTheme: RadioThemeData(
      fillColor: WidgetStateProperty.resolveWith(
        (state) => state.contains(WidgetState.selected) ? Warna.utama : Warna.garisIsian,
      ),
    ),
    switchTheme: SwitchThemeData(
      thumbColor: WidgetStateProperty.resolveWith(
        (state) => state.contains(WidgetState.selected) ? Colors.white : Warna.garisIsian,
      ),
      trackColor: WidgetStateProperty.resolveWith(
        (state) => state.contains(WidgetState.selected) ? Warna.utama : Colors.white,
      ),
      trackOutlineColor: WidgetStateProperty.resolveWith(
        (state) => state.contains(WidgetState.selected) ? Warna.utama : Warna.garisIsian,
      ),
    ),
  );
}
