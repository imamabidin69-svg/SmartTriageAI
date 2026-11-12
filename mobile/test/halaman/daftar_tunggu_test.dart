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

  testWidgets('kartu pasien ICU, ringkasan level, keterisian bed, dan penanda', (tester) async {
    aturAntrean(
      repo,
      items: [
        jsonItemTunggu(
          id: idKunjunganDua,
          nama: 'Sri Wahyuni',
          level: 'kritis',
          idTriaseTerakhir: idTriaseKritis,
          bed: 'ICU-1',
          skor: 11,
          peluang: 0.8123,
          lama: 3,
          batas: 15,
          tanda: 'normal',
        ),
        jsonItemTunggu(),
        jsonItemTunggu(
          id: 'k3',
          nama: 'Dewi Anggraini',
          level: 'sedang',
          bed: 'ICU-3',
          diagnosis: null,
          skor: 3,
          peluang: null,
          lama: 18,
          batas: 60,
          tanda: 'normal',
          menungguValidasi: false,
          eirSiap: true,
        ),
        jsonItemTunggu(
          id: 'k4',
          nama: 'Agus Pratama',
          level: null,
          bed: 'ICU-8',
          lama: 75,
          batas: null,
          tanda: 'belum_dinilai',
        ),
        jsonItemTunggu(
          id: 'k5',
          nama: 'Hartini',
          level: 'rendah',
          bed: 'ICU-5',
          status: 'ditangani',
          lama: 20,
          batas: 120,
          tanda: 'normal',
          review: true,
          statusValidasi: 'menunggu_review_dokter',
        ),
      ],
      daftarPeringatan: [peringatan()],
    );
    final semantik = tester.ensureSemantics();
    await jalankanAplikasi(tester, repo);

    // Ringkasan level dalam satu baris angka, keterisian bed, dan jam terakhir diperbarui.
    for (final label in ['Kritis: 1', 'Tinggi: 1', 'Sedang: 1', 'Rendah: 1', 'Belum dinilai: 1']) {
      expect(find.bySemanticsLabel('$label pasien'), findsOneWidget, reason: label);
    }
    expect(find.text('5 dari 8 bed terisi'), findsOneWidget);
    expect(find.textContaining('Diperbarui '), findsOneWidget);
    expect(find.text('Prioritas Pasien ICU'), findsOneWidget);

    expect(find.text('Peringatan'), findsWidgets);
    expect(find.text('Sri Wahyuni: Level naik dari Tinggi ke Kritis dan menunggu persetujuan dokter.'), findsOneWidget);
    expect(find.text('ICU-1'), findsOneWidget);
    expect(find.text('NEWS2 11 · peluang memburuk 81%'), findsOneWidget);
    expect(find.text('Observasi 3 mnt lalu'), findsOneWidget);
    expect(find.text('interval 15 mnt'), findsOneWidget);
    expect(find.text('Menunggu persetujuan dokter'), findsNWidgets(2));
    expect(find.text('Observasi terlambat'), findsOneWidget);
    expect(find.text('lewat interval 30 mnt'), findsOneWidget);
    expect(find.text('45 th · L · Syok sepsis'), findsWidgets);
    await tester.scrollUntilVisible(find.text('Hartini'), 200);
    expect(find.text('NEWS2 3'), findsOneWidget);
    expect(find.text('Ringkasan Eir siap'), findsOneWidget);
    expect(find.text('Belum dinilai'), findsOneWidget);
    expect(find.text('Belum dinilai · masuk 08.42'), findsOneWidget);
    expect(find.text('Masuk 1 jam 15 mnt lalu'), findsOneWidget);
    expect(find.text('Review diajukan'), findsOneWidget);
    expect(find.text('Sedang tindakan'), findsOneWidget);
    // Badge jumlah peringatan di kepala halaman.
    expect(find.byTooltip('1 peringatan'), findsOneWidget);
    await tutupAplikasi(tester);
    semantik.dispose();
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
    expect(find.text('Belum ada pasien yang dirawat di ICU.'), findsOneWidget);
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
    expect(find.textContaining('Menunggu persetujuan dokter: Sri Wahyuni'), findsOneWidget);

    // Peringatan yang sama tidak dimunculkan lagi.
    await tester.pump(const Duration(seconds: 15));
    await tester.pumpAndSettle();
    expect(find.byType(SnackBar), findsOneWidget);

    // Toast bisa langsung membuka hasil penilaian pasien.
    when(() => repo.detailTriase(idTriaseKritis))
        .thenAnswer((_) async => triaseDetail(id: idTriaseKritis, level: 'kritis'));
    await tester.tap(find.text('Lihat'));
    await tester.pumpAndSettle();
    expect(find.text('Hasil Penilaian'), findsOneWidget);
    await tutupAplikasi(tester);
  });

  testWidgets('beberapa peringatan baru sekaligus diringkas dalam satu toast', (tester) async {
    aturAntrean(repo);
    await jalankanAplikasi(tester, repo);
    when(() => repo.peringatan()).thenAnswer(
      (_) async => [
        peringatan(),
        peringatan(jenis: 'informasi_penting_eir', nama: 'Hartini', alasan: 'Alergi obat', idTriaseItem: null),
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
          jenis: 'informasi_penting_eir',
          nama: 'Hartini',
          alasan: 'Alergi obat',
          idTriaseItem: null,
          idKunjunganItem: idKunjungan,
        ),
      ],
    );
    when(() => repo.ringkasanEir(idKunjungan)).thenAnswer(
      (_) async => ringkasanEir(
        status: 'berjalan',
        denganRingkasan: false,
        tandaBahaya: 'Alergi obat; Memakai obat pengencer darah',
      ),
    );
    await jalankanAplikasi(tester, repo);

    await tester.tap(find.byTooltip('1 peringatan'));
    await tester.pumpAndSettle();
    expect(find.text('Hartini: Informasi penting dari keluarga'), findsOneWidget);
    await tester.tap(find.text('Hartini: Informasi penting dari keluarga'));
    await tester.pumpAndSettle();
    expect(find.text('Percakapan Eir'), findsOneWidget);
    expect(find.text('• Alergi obat\n• Memakai obat pengencer darah'), findsOneWidget);
    await kembali(tester);

    await tester.tap(find.text('Hartini: Alergi obat'));
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

  testWidgets('perawat membuka hasil, form observasi, dan kode QR dari kartu', (tester) async {
    aturAntrean(
      repo,
      items: [
        jsonItemTunggu(),
        jsonItemTunggu(id: 'k4', nama: 'Agus Pratama', level: null, bed: 'ICU-8', tanda: 'belum_dinilai', batas: null),
      ],
    );
    when(() => repo.detailTriase(idTriase)).thenAnswer((_) async => triaseDetail());
    when(() => repo.tautanEir(idKunjungan)).thenAnswer((_) async => tautanEir());
    await jalankanAplikasi(tester, repo);

    await tester.tap(find.text('Budi Santoso'));
    await tester.pumpAndSettle();
    expect(find.text('Hasil Penilaian'), findsOneWidget);
    await kembali(tester);

    await tester.tap(find.text('Observasi'));
    await tester.pumpAndSettle();
    expect(find.text('Observasi Pasien'), findsOneWidget);
    expect(find.text('Observasi · Bed ICU-2'), findsOneWidget);
    await kembali(tester);

    await ketuk(tester, find.text('QR Eir').first);
    expect(find.textContaining('Berlaku sampai'), findsOneWidget);
    await kembali(tester);

    await ketuk(tester, find.text('Nilai awal'));
    expect(find.text('Penilaian Awal'), findsOneWidget);
    await kembali(tester);

    await ketuk(tester, find.text('Agus Pratama'));
    expect(find.text('Penilaian Awal'), findsOneWidget);
    await tutupAplikasi(tester);
  });

  testWidgets('dokter tidak melihat tombol observasi dan tab Pasien Masuk', (tester) async {
    aturAntrean(
      repo,
      items: [
        jsonItemTunggu(),
        jsonItemTunggu(id: 'k4', nama: 'Agus Pratama', level: null, tanda: 'belum_dinilai', batas: null),
      ],
    );
    await jalankanAplikasi(tester, repo, peran: 'dokter');
    expect(find.text('Pasien Masuk'), findsNothing);
    expect(find.text('Observasi'), findsNothing);
    expect(find.text('QR Eir'), findsNothing);
    await ketuk(tester, find.text('Agus Pratama'));
    expect(find.text('Pasien ini belum dinilai perawat.'), findsOneWidget);

    // Navigasi bawah dokter: Prioritas, Riwayat, Profil.
    await tester.tap(find.text('Profil'));
    await tester.pumpAndSettle();
    expect(find.text('dr. Bagus Kurniawan'), findsOneWidget);
    await tester.tap(find.text('Riwayat'));
    await tester.pumpAndSettle();
    expect(find.text('Riwayat Pasien'), findsOneWidget);
    await tester.tap(find.text('Prioritas'));
    await tester.pumpAndSettle();
    expect(find.text('Prioritas Pasien ICU'), findsOneWidget);
    await tutupAplikasi(tester);
  });

  test('kunci peringatan membedakan jenis, kunjungan, triase, dan sesi', () {
    final a = peringatan();
    final b = peringatan(jenis: 'observasi_terlambat');
    expect(kunciPeringatan(a), isNot(kunciPeringatan(b)));
    expect(kunciPeringatan(a), kunciPeringatan(peringatan()));
    expect(ItemPeringatanJenis.menungguPersetujuan.json, 'menunggu_persetujuan');
  });
}
