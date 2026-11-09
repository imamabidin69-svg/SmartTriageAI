import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:smarttriage_mobile/api/galat_api.dart';
import 'package:smarttriage_mobile/api/generated/export.dart';
import 'package:smarttriage_mobile/state/antrean.dart';

import '../bantuan/aplikasi.dart';
import '../bantuan/data.dart';

void main() {
  late RepoTiruan repo;

  setUpAll(daftarkanNilaiCadangan);
  setUp(() => repo = RepoTiruan());

  testWidgets('kartu pasien, ringkasan level, dan tanda seperti mockup Gambar 7.1', (tester) async {
    aturAntrean(
      repo,
      items: [
        jsonItemTunggu(
          id: idKunjunganDua,
          nama: 'Sri Wahyuni',
          level: 'kritis',
          idTriaseTerakhir: idTriaseKritis,
          keluhan: 'Sesak napas sejak pagi',
          lama: 3,
          batas: null,
          tanda: 'normal',
        ),
        jsonItemTunggu(),
        jsonItemTunggu(
          id: 'k3',
          nama: 'Dewi Anggraini',
          level: 'sedang',
          keluhan: 'Demam tiga hari',
          lama: 18,
          batas: 30,
          tanda: 'normal',
          eirSiap: true,
        ),
        jsonItemTunggu(id: 'k4', nama: 'Agus Pratama', level: null, lama: 75, batas: null, tanda: 'belum_ditriase'),
        jsonItemTunggu(
          id: 'k5',
          nama: 'Hartini',
          level: 'rendah',
          keluhan: 'Luka lecet',
          lama: 20,
          batas: 60,
          tanda: 'normal',
          review: true,
          statusValidasi: 'menunggu_review_dokter',
        ),
      ],
      daftarPeringatan: [peringatan()],
    );
    await jalankanAplikasi(tester, repo);

    expect(find.text('Peringatan'), findsWidgets);
    expect(find.text('Sri Wahyuni: risk level kritis (SpO2 88%)'), findsOneWidget);
    expect(find.text('3 mnt · segera'), findsOneWidget);
    expect(find.text('Menunggu dokter'), findsOneWidget);
    expect(find.text('Perlu triase ulang'), findsOneWidget);
    expect(find.text('12 mnt / batas 10'), findsOneWidget);
    expect(find.text('45 th · L · datang 08.42'), findsWidgets);
    await tester.scrollUntilVisible(find.text('Hartini'), 200);
    expect(find.text('Ringkasan Eir siap'), findsOneWidget);
    expect(find.text('Belum ditriase'), findsWidgets);
    expect(find.text('1 jam 15 mnt sejak datang'), findsOneWidget);
    expect(find.text('Menunggu review dokter'), findsOneWidget);
    // Badge jumlah peringatan di kepala halaman.
    expect(find.byTooltip('1 peringatan'), findsOneWidget);
    await tutupAplikasi(tester);
  });

  testWidgets('daftar kosong dan error saat memuat pertama kali', (tester) async {
    var gagal = true;
    when(() => repo.daftarTunggu()).thenAnswer((_) async {
      if (gagal) {
        throw const GalatApi(status: 0, tipe: GalatApi.tipeJaringan, judul: 'Tidak dapat terhubung ke server.');
      }
      return daftarTunggu([]);
    });
    when(() => repo.peringatan()).thenAnswer((_) async => []);
    await jalankanAplikasi(tester, repo);
    expect(find.text('Tidak dapat terhubung ke server.'), findsOneWidget);

    gagal = false;
    await tester.tap(find.text('Coba lagi'));
    await tester.pumpAndSettle();
    expect(find.text('Tidak ada pasien yang menunggu dokter.'), findsOneWidget);
    await tutupAplikasi(tester);
  });

  testWidgets('dimuat ulang tiap 15 detik, peringatan baru muncul sebagai toast (TC-12)', (tester) async {
    aturAntrean(repo);
    await jalankanAplikasi(tester, repo);
    verify(() => repo.daftarTunggu()).called(1);

    when(() => repo.peringatan()).thenAnswer((_) async => [peringatan()]);
    await tester.pump(const Duration(seconds: 15));
    await tester.pumpAndSettle();
    verify(() => repo.daftarTunggu()).called(1);
    expect(find.textContaining('Risk level kritis: Sri Wahyuni'), findsOneWidget);

    // Peringatan yang sama tidak dimunculkan lagi.
    await tester.pump(const Duration(seconds: 15));
    await tester.pumpAndSettle();
    expect(find.byType(SnackBar), findsOneWidget);

    // Toast bisa langsung membuka hasil triase pasien.
    when(() => repo.detailTriase(idTriaseKritis))
        .thenAnswer((_) async => triaseDetail(id: idTriaseKritis, level: 'kritis'));
    await tester.tap(find.text('Lihat'));
    await tester.pumpAndSettle();
    expect(find.text('Hasil Triase'), findsOneWidget);
    await tutupAplikasi(tester);
  });

  testWidgets('beberapa peringatan baru sekaligus diringkas dalam satu toast', (tester) async {
    aturAntrean(repo);
    await jalankanAplikasi(tester, repo);
    when(() => repo.peringatan()).thenAnswer(
      (_) async => [
        peringatan(),
        peringatan(jenis: 'tanda_bahaya_eir', nama: 'Hartini', alasan: 'nyeri dada hebat', idTriaseItem: null),
      ],
    );
    await tester.pump(const Duration(seconds: 15));
    await tester.pumpAndSettle();
    expect(find.text('2 peringatan baru, salah satunya Sri Wahyuni.'), findsOneWidget);
    await tutupAplikasi(tester);
  });

  testWidgets('gagal memuat ulang tetap menampilkan data terakhir', (tester) async {
    aturAntrean(repo);
    await jalankanAplikasi(tester, repo);
    when(() => repo.daftarTunggu())
        .thenThrow(const GalatApi(status: 0, tipe: GalatApi.tipeJaringan, judul: 'Tidak dapat terhubung ke server.'));
    await tester.pump(const Duration(seconds: 15));
    await tester.pumpAndSettle();
    expect(find.textContaining('data terakhir yang berhasil dimuat'), findsOneWidget);
    expect(find.text('Budi Santoso'), findsOneWidget);
    await tutupAplikasi(tester);
  });

  testWidgets('tarik ke bawah memuat ulang', (tester) async {
    aturAntrean(repo);
    await jalankanAplikasi(tester, repo);
    await tester.fling(find.text('Budi Santoso'), const Offset(0, 400), 1000);
    await tester.pumpAndSettle();
    verify(() => repo.daftarTunggu()).called(2);
    await tutupAplikasi(tester);
  });

  testWidgets('aplikasi di latar belakang berhenti memuat ulang', (tester) async {
    aturAntrean(repo);
    await jalankanAplikasi(tester, repo);
    tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.inactive);
    tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.hidden);
    await tester.pump(const Duration(seconds: 45));
    verify(() => repo.daftarTunggu()).called(1);

    tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.inactive);
    tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.resumed);
    await tester.pumpAndSettle();
    verify(() => repo.daftarTunggu()).called(1);
    await tutupAplikasi(tester);
  });

  testWidgets('panel dan lembar peringatan membuka halaman terkait', (tester) async {
    aturAntrean(
      repo,
      daftarPeringatan: [
        peringatan(
          jenis: 'tanda_bahaya_eir',
          nama: 'Hartini',
          alasan: 'nyeri dada hebat',
          idTriaseItem: null,
          idKunjunganItem: idKunjungan,
        ),
      ],
    );
    when(() => repo.ringkasanEir(idKunjungan)).thenAnswer(
      (_) async => ringkasanEir(status: 'dihentikan', denganRingkasan: false, tandaBahaya: 'Nyeri dada hebat'),
    );
    await jalankanAplikasi(tester, repo);

    await tester.tap(find.byTooltip('1 peringatan'));
    await tester.pumpAndSettle();
    expect(find.text('Hartini: Tanda bahaya dari Eir'), findsOneWidget);
    await tester.tap(find.text('Hartini: Tanda bahaya dari Eir'));
    await tester.pumpAndSettle();
    expect(find.text('Percakapan Eir'), findsOneWidget);
    expect(find.text('Nyeri dada hebat'), findsOneWidget);
    await kembali(tester);

    await tester.tap(find.text('Hartini: nyeri dada hebat'));
    await tester.pumpAndSettle();
    expect(find.text('Percakapan Eir'), findsOneWidget);
    await tutupAplikasi(tester);
  });

  testWidgets('lembar peringatan kosong', (tester) async {
    aturAntrean(repo);
    await jalankanAplikasi(tester, repo);
    await tester.tap(find.byTooltip('Peringatan'));
    await tester.pumpAndSettle();
    expect(find.text('Tidak ada peringatan.'), findsOneWidget);
    await tutupAplikasi(tester);
  });

  testWidgets('perawat membuka hasil, form triase ulang, dan kode QR dari kartu', (tester) async {
    aturAntrean(
      repo,
      items: [
        jsonItemTunggu(),
        jsonItemTunggu(
          id: 'k5',
          nama: 'Hartini',
          level: 'rendah',
          keluhan: 'Luka lecet',
          tanda: 'normal',
          batas: 60,
          lama: 20,
        ),
        jsonItemTunggu(id: 'k4', nama: 'Agus Pratama', level: null, tanda: 'belum_ditriase', batas: null),
      ],
    );
    when(() => repo.detailTriase(idTriase)).thenAnswer((_) async => triaseDetail());
    when(() => repo.tautanEir('k5')).thenAnswer((_) async => tautanEir());
    await jalankanAplikasi(tester, repo);

    await tester.tap(find.text('Budi Santoso'));
    await tester.pumpAndSettle();
    expect(find.text('Hasil Triase'), findsOneWidget);
    await kembali(tester);

    await tester.tap(find.text('Triase ulang'));
    await tester.pumpAndSettle();
    expect(find.text('Form Triase'), findsOneWidget);
    expect(find.text('Triase ulang'), findsOneWidget);
    await kembali(tester);

    await ketuk(tester, find.text('Kode QR Eir'));
    expect(find.textContaining('Berlaku sampai'), findsOneWidget);
    await kembali(tester);

    await ketuk(tester, find.text('Agus Pratama'));
    expect(find.text('Form Triase'), findsOneWidget);
    await tutupAplikasi(tester);
  });

  testWidgets('dokter tidak melihat tombol triase dan tab Triase Baru', (tester) async {
    aturAntrean(
      repo,
      items: [
        jsonItemTunggu(),
        jsonItemTunggu(id: 'k4', nama: 'Agus Pratama', level: null, tanda: 'belum_ditriase', batas: null),
      ],
    );
    await jalankanAplikasi(tester, repo, peran: 'dokter');
    expect(find.text('Triase Baru'), findsNothing);
    expect(find.text('Triase ulang'), findsNothing);
    await ketuk(tester, find.text('Agus Pratama'));
    expect(find.text('Pasien ini belum ditriase perawat.'), findsOneWidget);

    // Navigasi bawah dokter: Daftar Tunggu, Riwayat, Profil.
    await tester.tap(find.text('Profil'));
    await tester.pumpAndSettle();
    expect(find.text('dr. Bagus Kurniawan'), findsOneWidget);
    await tester.tap(find.text('Riwayat'));
    await tester.pumpAndSettle();
    expect(find.text('Riwayat Pasien'), findsOneWidget);
    await tester.tap(find.text('Daftar Tunggu'));
    await tester.pumpAndSettle();
    expect(find.text('Daftar Tunggu IGD'), findsOneWidget);
    await tutupAplikasi(tester);
  });

  test('kunci peringatan membedakan jenis, kunjungan, triase, dan sesi', () {
    final a = peringatan();
    final b = peringatan(jenis: 'level_naik');
    expect(kunciPeringatan(a), isNot(kunciPeringatan(b)));
    expect(kunciPeringatan(a), kunciPeringatan(peringatan()));
    expect(ItemPeringatanJenis.kritisBelumDivalidasi.json, 'kritis_belum_divalidasi');
  });
}
