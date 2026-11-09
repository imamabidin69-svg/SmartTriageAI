import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:smarttriage_mobile/api/galat_api.dart';
import 'package:smarttriage_mobile/state/sesi.dart';

import '../bantuan/aplikasi.dart';
import '../bantuan/data.dart';

void main() {
  late RepoTiruan repo;

  setUpAll(daftarkanNilaiCadangan);
  setUp(() {
    repo = RepoTiruan();
    aturAntrean(repo);
  });

  testWidgets('belum login diarahkan ke halaman Masuk, lalu masuk ke daftar tunggu (TC-01)', (tester) async {
    await jalankanAplikasi(tester, repo, peran: null);
    expect(find.text('Untuk perawat dan dokter IGD.'), findsOneWidget);

    when(() => repo.masuk('perawat@smarttriage.demo', 'rahasia123')).thenAnswer((_) async => pengguna('perawat'));
    await tester.enterText(find.widgetWithText(TextFormField, 'Email'), ' perawat@smarttriage.demo ');
    await tester.enterText(find.widgetWithText(TextFormField, 'Password'), 'rahasia123');
    await tester.tap(find.widgetWithText(FilledButton, 'Masuk'));
    await tester.pumpAndSettle();

    expect(find.text('Daftar Tunggu IGD'), findsOneWidget);
    expect(find.text('Budi Santoso'), findsOneWidget);
    await tutupAplikasi(tester);
  });

  testWidgets('memeriksa isian sebelum dikirim', (tester) async {
    await jalankanAplikasi(tester, repo, peran: null);
    await tester.tap(find.widgetWithText(FilledButton, 'Masuk'));
    await tester.pump();
    expect(find.text('Email wajib diisi.'), findsOneWidget);
    expect(find.text('Password wajib diisi.'), findsOneWidget);

    await tester.enterText(find.widgetWithText(TextFormField, 'Email'), 'bukan-email');
    await tester.tap(find.widgetWithText(FilledButton, 'Masuk'));
    await tester.pump();
    expect(find.text('Format email tidak valid.'), findsOneWidget);
    verifyNever(() => repo.masuk(any(), any()));
    await tutupAplikasi(tester);
  });

  testWidgets('password salah dan batas percobaan ditampilkan', (tester) async {
    await jalankanAplikasi(tester, repo, peran: null);
    when(() => repo.masuk(any(), any()))
        .thenThrow(const GalatApi(status: 401, tipe: GalatApi.tipeKredensialSalah, judul: 'Email atau password salah'));
    await tester.enterText(find.widgetWithText(TextFormField, 'Email'), 'perawat@smarttriage.demo');
    await tester.enterText(find.widgetWithText(TextFormField, 'Password'), 'salah');
    await tester.testTextInput.receiveAction(TextInputAction.done);
    await tester.pumpAndSettle();
    expect(find.text('Periksa kembali email dan password Anda.'), findsOneWidget);

    when(() => repo.masuk(any(), any())).thenThrow(
      const GalatApi(
        status: 429,
        tipe: 'urn:smarttriage:problem:terlalu-banyak-percobaan',
        judul: 'Terlalu banyak percobaan',
        detail: 'Coba lagi dalam 15 menit.',
      ),
    );
    await tester.tap(find.widgetWithText(FilledButton, 'Masuk'));
    await tester.pumpAndSettle();
    expect(find.text('Coba lagi dalam 15 menit.'), findsOneWidget);
    await tutupAplikasi(tester);
  });

  testWidgets('akun admin ditolak dan sesinya dihapus', (tester) async {
    await jalankanAplikasi(tester, repo, peran: null);
    when(() => repo.masuk(any(), any())).thenAnswer((_) async => pengguna('admin'));
    when(() => repo.keluar()).thenAnswer((_) async {});
    await tester.enterText(find.widgetWithText(TextFormField, 'Email'), 'admin@smarttriage.demo');
    await tester.enterText(find.widgetWithText(TextFormField, 'Password'), 'rahasia123');
    await tester.tap(find.widgetWithText(FilledButton, 'Masuk'));
    await tester.pumpAndSettle();
    expect(find.text(pesanBukanStafMedis), findsOneWidget);
    verify(() => repo.keluar()).called(1);
    await tutupAplikasi(tester);
  });

  testWidgets('tombol mata menampilkan password', (tester) async {
    await jalankanAplikasi(tester, repo, peran: null);
    await tester.tap(find.byTooltip('Tampilkan password'));
    await tester.pump();
    expect(find.byTooltip('Sembunyikan password'), findsOneWidget);
    await tutupAplikasi(tester);
  });

  testWidgets('server tidak terjangkau saat aplikasi dibuka, lalu dicoba lagi', (tester) async {
    when(() => repo.adaSesiTersimpan()).thenAnswer((_) async => true);
    var panggilan = 0;
    when(() => repo.saya()).thenAnswer((_) async {
      panggilan++;
      if (panggilan == 1) throw const GalatApi(status: 0, tipe: GalatApi.tipeJaringan, judul: 'Tidak dapat terhubung.');
      return pengguna('dokter');
    });
    await jalankanAplikasi(tester, repo, aturSesi: false);
    expect(find.text('Tidak dapat terhubung.'), findsOneWidget);
    await tester.tap(find.text('Coba lagi'));
    await tester.pumpAndSettle();
    expect(find.text('Daftar Tunggu IGD'), findsOneWidget);
    // Dokter tidak melihat tab Triase Baru.
    expect(find.text('Triase Baru'), findsNothing);
    await tutupAplikasi(tester);
  });

  testWidgets('token tersimpan yang sudah ditolak server kembali ke halaman Masuk', (tester) async {
    when(() => repo.adaSesiTersimpan()).thenAnswer((_) async => true);
    when(() => repo.saya())
        .thenThrow(const GalatApi(status: 401, tipe: GalatApi.tipeTidakTerautentikasi, judul: 'Sesi berakhir'));
    when(() => repo.hapusSesi()).thenAnswer((_) async {});
    await jalankanAplikasi(tester, repo, aturSesi: false);
    expect(find.text('Untuk perawat dan dokter IGD.'), findsOneWidget);
    verify(() => repo.hapusSesi()).called(1);
    await tutupAplikasi(tester);
  });

  testWidgets('token tersimpan milik admin dihapus', (tester) async {
    when(() => repo.adaSesiTersimpan()).thenAnswer((_) async => true);
    when(() => repo.saya()).thenAnswer((_) async => pengguna('admin'));
    when(() => repo.hapusSesi()).thenAnswer((_) async {});
    await jalankanAplikasi(tester, repo, aturSesi: false);
    expect(find.text('Untuk perawat dan dokter IGD.'), findsOneWidget);
    await tutupAplikasi(tester);
  });
}
