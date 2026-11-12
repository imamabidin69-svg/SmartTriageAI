/// Menjalankan aplikasi utuh di widget test dengan repository tiruan, seukuran layar ponsel 360 x 800.
library;

import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:smarttriage_mobile/api/generated/export.dart';
import 'package:smarttriage_mobile/api/repositori.dart';
import 'package:smarttriage_mobile/main.dart';
import 'package:smarttriage_mobile/router.dart';
import 'package:smarttriage_mobile/state/penyedia.dart';

import 'data.dart';

class RepoTiruan extends Mock implements RepositoriApi {}

void daftarkanNilaiCadangan() {
  registerFallbackValue(
    const TriaseInput(
      tingkatKesadaran: TingkatKesadaran.a,
      oksigenTambahan: false,
      catatan: null,
      tandaVital: TandaVital(tdSistolik: 0, tdDiastolik: 0, nadi: 0, lajuNapas: 0, suhu: 36, saturasi: 98),
      idPemindaian: [],
    ),
  );
  registerFallbackValue(const ValidasiRequest(aksi: ValidasiRequestAksi.setujui, riskLevel: null, alasan: null));
  registerFallbackValue(
    const RegistrasiRequest(
      idPasien: null,
      nama: null,
      tanggalLahir: null,
      perkiraanUsia: null,
      jenisKelamin: null,
      nik: null,
      noTelepon: null,
      nomorBed: 'ICU-1',
      asalRuangan: null,
      diagnosisMasuk: null,
    ),
  );
  registerFallbackValue(JenisAlat.tensimeter);
  registerFallbackValue(StatusKunjunganRequestStatus.ditangani);
  registerFallbackValue(File('foto.jpg'));
}

/// Daftar tunggu dan peringatan yang dikembalikan repository tiruan.
void aturAntrean(
  RepoTiruan repo, {
  List<Map<String, Object?>>? items,
  List<ItemPeringatan> daftarPeringatan = const [],
}) {
  when(() => repo.daftarTunggu()).thenAnswer((_) async => daftarTunggu(items ?? [jsonItemTunggu()]));
  when(() => repo.peringatan()).thenAnswer((_) async => daftarPeringatan);
}

/// Memasang aplikasi. [peran] null berarti belum login.
Future<ProviderContainer> jalankanAplikasi(
  WidgetTester tester,
  RepoTiruan repo, {
  String? peran = 'perawat',
  PengambilFoto? kamera,
  bool tungguSelesai = true,
  bool aturSesi = true,
}) async {
  tester.view.physicalSize = const Size(1080, 2400);
  tester.view.devicePixelRatio = 3;
  addTearDown(tester.view.reset);
  if (!aturSesi) {
    // Sesi sudah diatur sendiri oleh tes.
  } else if (peran == null) {
    when(() => repo.adaSesiTersimpan()).thenAnswer((_) async => false);
  } else {
    when(() => repo.adaSesiTersimpan()).thenAnswer((_) async => true);
    when(() => repo.saya()).thenAnswer((_) async => pengguna(peran));
  }
  await tester.pumpWidget(
    ProviderScope(
      retry: (_, _) => null,
      overrides: [
        repositoriProvider.overrideWithValue(repo),
        if (kamera != null) pengambilFotoProvider.overrideWithValue(kamera),
      ],
      child: const AplikasiSmartTriage(),
    ),
  );
  if (tungguSelesai) await tester.pumpAndSettle();
  return ProviderScope.containerOf(tester.element(find.byType(AplikasiSmartTriage)));
}

/// Membuka halaman lewat router, seperti pengguna menekan tautan.
Future<void> bukaHalaman(WidgetTester tester, ProviderContainer container, String lokasi, {Object? extra}) async {
  unawaited(container.read(routerProvider).push<Object?>(lokasi, extra: extra));
  await tester.pumpAndSettle();
}

/// Melepas aplikasi supaya pewaktu daftar tunggu ikut berhenti sebelum tes selesai.
Future<void> tutupAplikasi(WidgetTester tester) async {
  await tester.pumpWidget(const SizedBox());
  await tester.pump();
}

/// ListView membangun anaknya bertahap, jadi widget di bawah layar digulir dulu sampai ada.
Future<void> gulirSampaiAda(WidgetTester tester, Finder finder) async {
  if (finder.evaluate().isEmpty) {
    await tester.scrollUntilVisible(finder, 300, scrollable: find.byType(Scrollable).first);
  }
  await tester.ensureVisible(finder);
}

/// Menggulir sampai widget terlihat lalu mengetuknya.
Future<void> ketuk(WidgetTester tester, Finder finder) async {
  await gulirSampaiAda(tester, finder);
  await tester.pumpAndSettle();
  await tester.tap(finder);
  await tester.pumpAndSettle();
}

Future<void> isi(WidgetTester tester, Finder finder, String teks) async {
  await gulirSampaiAda(tester, finder);
  await tester.enterText(finder, teks);
  await tester.pump();
}

/// Menekan tombol kembali di AppBar. pageBack() bawaan mencari tooltip berbahasa Inggris "Back".
Future<void> kembali(WidgetTester tester) async {
  await tester.tap(find.byTooltip('Kembali').last);
  await tester.pumpAndSettle();
}

/// Menggulir ke atas sampai widget terlihat, misalnya status di atas halaman setelah menekan tombol di bawah.
Future<void> gulirKeAtasSampaiAda(WidgetTester tester, Finder finder) async {
  if (finder.evaluate().isEmpty) {
    await tester.scrollUntilVisible(finder, -300, scrollable: find.byType(Scrollable).first);
  }
  await tester.ensureVisible(finder);
  await tester.pumpAndSettle();
}
