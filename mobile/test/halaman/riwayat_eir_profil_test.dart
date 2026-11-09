import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:smarttriage_mobile/api/galat_api.dart';
import 'package:smarttriage_mobile/rute.dart';

import '../bantuan/aplikasi.dart';
import '../bantuan/data.dart';

void main() {
  late RepoTiruan repo;

  setUpAll(daftarkanNilaiCadangan);
  setUp(() {
    repo = RepoTiruan();
    aturAntrean(repo);
  });

  group('Riwayat', () {
    testWidgets('mencari pasien, membuka riwayat, memuat lebih banyak, lalu membuka hasil (FR-09)', (tester) async {
      when(() => repo.cariPasien('budi')).thenAnswer((_) async => [pasienRingkas()]);
      when(() => repo.riwayat(idPasien)).thenAnswer((_) async => riwayat(kursor: 'kursor-2'));
      when(() => repo.riwayat(idPasien, kursor: 'kursor-2'))
          .thenAnswer((_) async => riwayat(idTriaseItem: 'triase-lama', keluhan: 'Pusing berputar'));
      when(() => repo.detailTriase(idTriase)).thenAnswer((_) async => triaseDetail());
      await jalankanAplikasi(tester, repo);
      await tester.tap(find.text('Riwayat'));
      await tester.pumpAndSettle();
      expect(find.textContaining('Cari pasien untuk melihat'), findsOneWidget);

      await tester.enterText(find.byKey(const ValueKey('cari-riwayat')), 'b');
      await tester.testTextInput.receiveAction(TextInputAction.search);
      await tester.pumpAndSettle();
      expect(find.text('Ketik minimal 2 huruf nama, atau NIK lengkap.'), findsOneWidget);

      await tester.enterText(find.byKey(const ValueKey('cari-riwayat')), 'budi');
      await tester.tap(find.byTooltip('Cari'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Budi Santoso'));
      await tester.pumpAndSettle();

      expect(find.text('Riwayat Triase'), findsOneWidget);
      expect(find.text('Triase ulang · 2 Nov 2026 08.50'), findsOneWidget);
      expect(find.text('Disetujui · oleh Ns. Ratna Wijaya · Menunggu dokter'), findsOneWidget);
      await ketuk(tester, find.text('Muat lebih banyak'));
      expect(find.text('Pusing berputar'), findsOneWidget);
      expect(find.text('Muat lebih banyak'), findsNothing);

      await ketuk(tester, find.text('Nyeri dada kiri'));
      expect(find.text('Hasil Triase'), findsOneWidget);
      await tutupAplikasi(tester);
    });

    testWidgets('pasien tidak ditemukan, riwayat kosong, dan gagal dimuat', (tester) async {
      when(() => repo.cariPasien('zzz')).thenAnswer((_) async => []);
      var gagal = true;
      when(() => repo.riwayat(idPasien)).thenAnswer((_) async {
        if (gagal) throw const GalatApi(status: 0, tipe: GalatApi.tipeJaringan, judul: 'Tidak dapat terhubung.');
        return riwayatKosong();
      });
      final container = await jalankanAplikasi(tester, repo);
      await tester.tap(find.text('Riwayat'));
      await tester.pumpAndSettle();
      await tester.enterText(find.byKey(const ValueKey('cari-riwayat')), 'zzz');
      await tester.tap(find.byTooltip('Cari'));
      await tester.pumpAndSettle();
      expect(find.text('Pasien tidak ditemukan.'), findsOneWidget);

      await bukaHalaman(tester, container, Rute.riwayatPasien(idPasien));
      expect(find.text('Tidak dapat terhubung.'), findsOneWidget);
      gagal = false;
      await tester.tap(find.text('Coba lagi'));
      await tester.pumpAndSettle();
      expect(find.text('Pasien ini belum pernah ditriase.'), findsOneWidget);
      await tutupAplikasi(tester);
    });
  });

  group('Eir', () {
    testWidgets('kode QR Eir, salin tautan, dan buat kode baru (FR-08)', (tester) async {
      String? disalin;
      tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(SystemChannels.platform, (panggilan) async {
        if (panggilan.method == 'Clipboard.setData') disalin = (panggilan.arguments as Map)['text'] as String;
        return null;
      });
      addTearDown(() => tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(SystemChannels.platform, null));
      when(() => repo.tautanEir(idKunjungan)).thenAnswer((_) async => tautanEir());
      final container = await jalankanAplikasi(tester, repo);
      await bukaHalaman(tester, container, Rute.kodeQrEir(idKunjungan), extra: pasien());

      expect(find.text('Budi Santoso'), findsOneWidget);
      expect(find.text('Berlaku sampai 11.00 WIB'), findsOneWidget);
      await ketuk(tester, find.text('Salin tautan'));
      expect(disalin, 'http://192.168.1.10:5000/eir#t=token-eir');
      expect(find.text('Tautan Eir disalin.'), findsOneWidget);
      // Snackbar menutupi tombol di bawah layar, jadi ditunggu sampai hilang.
      await tester.pump(const Duration(seconds: 5));
      await tester.pumpAndSettle();
      await ketuk(tester, find.text('Buat kode baru'));
      verify(() => repo.tautanEir(idKunjungan)).called(2);
      await tutupAplikasi(tester);
    });

    testWidgets('kode QR ditolak untuk pasien yang bukan zona hijau', (tester) async {
      var gagal = true;
      when(() => repo.tautanEir(idKunjungan)).thenAnswer((_) async {
        if (gagal) {
          throw const GalatApi(
            status: 409,
            tipe: GalatApi.tipeKonflik,
            judul: 'Konflik',
            detail: 'Eir hanya untuk pasien dengan risk level terakhir rendah (zona hijau).',
          );
        }
        return tautanEir();
      });
      final container = await jalankanAplikasi(tester, repo);
      await bukaHalaman(tester, container, Rute.kodeQrEir(idKunjungan));
      expect(find.textContaining('zona hijau'), findsOneWidget);
      gagal = false;
      await tester.tap(find.text('Coba lagi'));
      await tester.pumpAndSettle();
      expect(find.textContaining('Berlaku sampai'), findsOneWidget);
      await tutupAplikasi(tester);
    });

    testWidgets('percakapan Eir yang selesai menampilkan ringkasan dan transkrip', (tester) async {
      when(() => repo.ringkasanEir(idKunjungan)).thenAnswer((_) async => ringkasanEir());
      final container = await jalankanAplikasi(tester, repo, peran: 'dokter');
      await bukaHalaman(tester, container, Rute.ringkasanEir(idKunjungan), extra: 'Dewi Anggraini');
      expect(find.text('Dewi Anggraini'), findsOneWidget);
      expect(find.text('Percakapan selesai · dijawab keluarga · mulai 08.55'), findsOneWidget);
      expect(find.text('Keluhan utama: Demam tiga hari'), findsOneWidget);
      expect(find.text('Kategori: Demam'), findsOneWidget);
      expect(find.text('Demam tiga hari'), findsOneWidget);
      await tutupAplikasi(tester);
    });

    testWidgets('percakapan masih berjalan atau gagal dimuat', (tester) async {
      var gagal = true;
      when(() => repo.ringkasanEir(idKunjungan)).thenAnswer((_) async {
        if (gagal) throw const GalatApi(status: 404, tipe: 'x', judul: 'Kunjungan ini belum punya sesi Eir.');
        return ringkasanEir(status: 'berjalan', denganRingkasan: false);
      });
      final container = await jalankanAplikasi(tester, repo);
      await bukaHalaman(tester, container, Rute.ringkasanEir(idKunjungan));
      expect(find.text('Kunjungan ini belum punya sesi Eir.'), findsOneWidget);
      gagal = false;
      await tester.tap(find.text('Coba lagi'));
      await tester.pumpAndSettle();
      expect(find.textContaining('Percakapan masih berjalan'), findsOneWidget);
      await tutupAplikasi(tester);
    });
  });

  group('Profil', () {
    testWidgets('mengganti password dengan pemeriksaan isian', (tester) async {
      when(() => repo.gantiPassword(lama: 'lama12345', baru: 'baru12345')).thenAnswer((_) async {});
      await jalankanAplikasi(tester, repo);
      await tester.tap(find.text('Profil'));
      await tester.pumpAndSettle();
      expect(find.text('Ns. Ratna Wijaya'), findsOneWidget);
      expect(find.text('Perawat'), findsOneWidget);
      expect(find.text('Server: http://10.0.2.2:5000'), findsOneWidget);

      await ketuk(tester, find.text('Simpan password'));
      expect(find.text('Password lama wajib diisi.'), findsOneWidget);
      expect(find.text('Password baru harus 8 sampai 128 karakter.'), findsOneWidget);

      await isi(tester, find.widgetWithText(TextFormField, 'Password lama'), 'lama12345');
      await isi(tester, find.widgetWithText(TextFormField, 'Password baru'), 'lama12345');
      await isi(tester, find.widgetWithText(TextFormField, 'Ulangi password baru'), 'beda');
      await ketuk(tester, find.text('Simpan password'));
      expect(find.text('Password baru harus berbeda dari password lama.'), findsOneWidget);
      expect(find.text('Ulangan password tidak sama.'), findsOneWidget);

      await isi(tester, find.widgetWithText(TextFormField, 'Password baru'), 'baru12345');
      await isi(tester, find.widgetWithText(TextFormField, 'Ulangi password baru'), 'baru12345');
      await ketuk(tester, find.text('Simpan password'));
      expect(find.text('Password berhasil diganti.'), findsOneWidget);
      await tutupAplikasi(tester);
    });

    testWidgets('penolakan server ditampilkan di kolom atau di atas form', (tester) async {
      await jalankanAplikasi(tester, repo, peran: 'dokter');
      await tester.tap(find.text('Profil'));
      await tester.pumpAndSettle();
      when(
        () => repo.gantiPassword(
          lama: any(named: 'lama'),
          baru: any(named: 'baru'),
        ),
      ).thenThrow(
        const GalatApi(
          status: 422,
          tipe: 'x',
          judul: 'Data tidak valid',
          pesanField: {'password_lama': 'Password lama salah.'},
        ),
      );
      await isi(tester, find.widgetWithText(TextFormField, 'Password lama'), 'salah123');
      await isi(tester, find.widgetWithText(TextFormField, 'Password baru'), 'baru12345');
      await isi(tester, find.widgetWithText(TextFormField, 'Ulangi password baru'), 'baru12345');
      await ketuk(tester, find.text('Simpan password'));
      expect(find.text('Password lama salah.'), findsOneWidget);

      when(
        () => repo.gantiPassword(
          lama: any(named: 'lama'),
          baru: any(named: 'baru'),
        ),
      ).thenThrow(
        const GalatApi(status: 429, tipe: 'x', judul: 'Terlalu banyak percobaan', detail: 'Coba lagi nanti.'),
      );
      await ketuk(tester, find.text('Simpan password'));
      await gulirKeAtasSampaiAda(tester, find.text('Coba lagi nanti.'));
      await tutupAplikasi(tester);
    });

    testWidgets('keluar kembali ke halaman Masuk', (tester) async {
      when(() => repo.keluar()).thenAnswer((_) async {});
      await jalankanAplikasi(tester, repo);
      await tester.tap(find.text('Profil'));
      await tester.pumpAndSettle();
      await ketuk(tester, find.text('Keluar'));
      await tester.tap(find.text('Batal'));
      await tester.pumpAndSettle();
      verifyNever(() => repo.keluar());

      await ketuk(tester, find.widgetWithText(OutlinedButton, 'Keluar'));
      await tester.tap(find.widgetWithText(FilledButton, 'Keluar'));
      await tester.pumpAndSettle();
      verify(() => repo.keluar()).called(1);
      expect(find.text('Untuk perawat dan dokter IGD.'), findsOneWidget);
      await tutupAplikasi(tester);
    });
  });
}
