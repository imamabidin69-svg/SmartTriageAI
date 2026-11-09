import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:smarttriage_mobile/api/galat_api.dart';
import 'package:smarttriage_mobile/api/generated/export.dart';
import 'package:smarttriage_mobile/halaman/hasil.dart';
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

  Future<void> bukaHasil(
    WidgetTester tester, {
    String peran = 'perawat',
    TriaseDetail? detail,
    StatusKunjungan? status = StatusKunjungan.menunggu,
  }) async {
    final container = await jalankanAplikasi(tester, repo, peran: peran);
    await bukaHalaman(
      tester,
      container,
      Rute.hasil(idTriase),
      extra: InfoHasil(detail: detail, statusKunjungan: status),
    );
  }

  testWidgets('menampilkan risk level, tiga faktor penjelas, dan data triase (FR-05)', (tester) async {
    when(() => repo.detailTriase(idTriase)).thenAnswer(
      (_) async => triaseDetail(
        peringatan: [
          {'field': 'tanda_vital.td_sistolik', 'pesan': 'Tekanan sistolik 158 di atas normal.'},
        ],
      ),
    );
    await bukaHasil(tester);
    expect(find.text('Tinggi'), findsOneWidget);
    expect(find.text('Menunggu validasi'), findsOneWidget);
    expect(find.text('Sumber: Model AI (Random Forest) (smarttriage-rf-v1.0.0)'), findsOneWidget);
    expect(find.text('Kategori keluhan: Nyeri dada'), findsOneWidget);
    expect(find.text('Nadi: 104'), findsOneWidget);
    expect(find.text('Usia'), findsOneWidget);
    // Hanya tiga faktor teratas yang ditampilkan.
    expect(find.textContaining('Suhu: 37,2'), findsNothing);
    await gulirSampaiAda(tester, find.text('• Tekanan sistolik 158 di atas normal.'));
    await gulirSampaiAda(tester, find.textContaining('TD 158/96'));
    expect(find.text('TD 158/96 · nadi 104 · napas 22 · suhu 37,2 °C · SpO₂ 95%'), findsOneWidget);
    expect(find.text('Sebagian dibaca dari foto'), findsOneWidget);
    await tutupAplikasi(tester);
  });

  testWidgets('aturan cadangan diberi keterangan', (tester) async {
    await bukaHasil(
      tester,
      detail: triaseDetail(sumber: 'aturan', status: 'disetujui', divalidasi: 'dr. Bagus', catatan: 'Sesuai'),
    );
    expect(find.text('Sumber: Aturan cadangan'), findsOneWidget);
    expect(find.textContaining('aturan cadangan dari ambang'), findsOneWidget);
    expect(find.text('menambah poin risiko'), findsWidgets);
    await gulirSampaiAda(tester, find.text('Divalidasi oleh'));
    expect(find.text('dr. Bagus'), findsOneWidget);
    expect(find.text('Sesuai'), findsOneWidget);
    // Sudah disetujui: tidak ada tombol validasi lagi.
    expect(find.text('Setujui'), findsNothing);
    await tutupAplikasi(tester);
  });

  testWidgets('gagal memuat lalu dicoba lagi', (tester) async {
    var gagal = true;
    when(() => repo.detailTriase(idTriase)).thenAnswer((_) async {
      if (gagal) throw const GalatApi(status: 404, tipe: 'x', judul: 'Triase tidak ditemukan.');
      return triaseDetail();
    });
    await bukaHasil(tester);
    expect(find.text('Triase tidak ditemukan.'), findsOneWidget);
    gagal = false;
    await tester.tap(find.text('Coba lagi'));
    await tester.pumpAndSettle();
    expect(find.text('Tinggi'), findsOneWidget);
    await tutupAplikasi(tester);
  });

  testWidgets('perawat menyetujui hasil non-kritis (TC-10)', (tester) async {
    when(() => repo.validasi(idTriase, any()))
        .thenAnswer((_) async => triaseDetail(status: 'disetujui', divalidasi: 'Ns. Ratna Wijaya'));
    await bukaHasil(tester, detail: triaseDetail());
    await ketuk(tester, find.widgetWithText(FilledButton, 'Setujui'));
    expect(find.text('Setujui hasil triase?'), findsOneWidget);
    await tester.tap(find.widgetWithText(FilledButton, 'Setujui').last);
    await tester.pumpAndSettle();

    final data = verify(() => repo.validasi(idTriase, captureAny())).captured.single as ValidasiRequest;
    expect(data.toJson(), {'aksi': 'setujui', 'risk_level': null, 'alasan': null});
    expect(find.text('Hasil triase disetujui.'), findsOneWidget);
    await gulirKeAtasSampaiAda(tester, find.text('Disetujui'));
    await tutupAplikasi(tester);
  });

  testWidgets('membatalkan persetujuan tidak mengirim apa pun', (tester) async {
    await bukaHasil(tester, detail: triaseDetail());
    await ketuk(tester, find.widgetWithText(FilledButton, 'Setujui'));
    await tester.tap(find.text('Batal'));
    await tester.pumpAndSettle();
    verifyNever(() => repo.validasi(any(), any()));
    await tutupAplikasi(tester);
  });

  testWidgets('hasil kritis tidak bisa disetujui perawat; ajuan review wajib beralasan', (tester) async {
    when(() => repo.validasi(idTriase, any()))
        .thenAnswer((_) async => triaseDetail(level: 'kritis', status: 'menunggu_review_dokter'));
    await bukaHasil(tester, detail: triaseDetail(level: 'kritis'));
    expect(find.widgetWithText(FilledButton, 'Setujui'), findsNothing);
    await gulirSampaiAda(tester, find.textContaining('Hasil kritis harus divalidasi dokter'));

    await ketuk(tester, find.text('Ajukan review dokter'));
    await tester.tap(find.text('Kirim'));
    await tester.pump();
    expect(find.text('Alasan minimal 5 karakter.'), findsOneWidget);
    await tester.enterText(find.widgetWithText(TextFormField, 'Alasan'), 'SpO2 turun, mohon dicek');
    await tester.tap(find.text('Kirim'));
    await tester.pumpAndSettle();

    final data = verify(() => repo.validasi(idTriase, captureAny())).captured.single as ValidasiRequest;
    expect(data.aksi, ValidasiRequestAksi.ajukanReview);
    expect(data.alasan, 'SpO2 turun, mohon dicek');
    expect(find.text('Review diajukan ke dokter.'), findsOneWidget);
    await gulirSampaiAda(tester, find.text('Menunggu review dokter.'));
    await tutupAplikasi(tester);
  });

  testWidgets('penolakan server ditampilkan', (tester) async {
    when(() => repo.validasi(idTriase, any())).thenThrow(
      const GalatApi(
        status: 409,
        tipe: GalatApi.tipeKonflik,
        judul: 'Konflik',
        detail: 'Triase ini sudah digantikan triase ulang yang lebih baru.',
      ),
    );
    await bukaHasil(tester, detail: triaseDetail());
    await ketuk(tester, find.widgetWithText(FilledButton, 'Setujui'));
    await tester.tap(find.widgetWithText(FilledButton, 'Setujui').last);
    await tester.pumpAndSettle();
    expect(find.text('Triase ini sudah digantikan triase ulang yang lebih baru.'), findsOneWidget);
    await tutupAplikasi(tester);
  });

  testWidgets('dokter mengoreksi risk level dengan alasan (TC-11)', (tester) async {
    when(() => repo.validasi(idTriase, any()))
        .thenAnswer((_) async => triaseDetail(level: 'kritis', status: 'dikoreksi'));
    await bukaHasil(
      tester,
      peran: 'dokter',
      detail: triaseDetail(status: 'menunggu_review_dokter'),
    );
    expect(find.text('Ajukan review dokter'), findsNothing);

    await ketuk(tester, find.text('Koreksi risk level'));
    expect(find.text('Level saat ini: Tinggi'), findsOneWidget);
    await tester.tap(find.text('Simpan koreksi'));
    await tester.pump();
    expect(find.text('Pilih level hasil koreksi.'), findsOneWidget);
    expect(find.text('Alasan minimal 5 karakter.'), findsOneWidget);

    await tester.tap(find.text('Kritis'));
    await tester.enterText(find.widgetWithText(TextFormField, 'Alasan koreksi'), 'Nyeri dada khas sindrom koroner');
    await tester.tap(find.text('Simpan koreksi'));
    await tester.pumpAndSettle();

    final data = verify(() => repo.validasi(idTriase, captureAny())).captured.single as ValidasiRequest;
    expect(data.toJson(), {'aksi': 'koreksi', 'risk_level': 'kritis', 'alasan': 'Nyeri dada khas sindrom koroner'});
    expect(find.text('Risk level dikoreksi menjadi kritis.'), findsOneWidget);
    await gulirKeAtasSampaiAda(tester, find.text('Dikoreksi dokter'));
    await tutupAplikasi(tester);
  });

  testWidgets('dokter menyetujui lalu mengubah status kunjungan', (tester) async {
    when(() => repo.validasi(idTriase, any())).thenAnswer((_) async => triaseDetail(status: 'disetujui'));
    when(() => repo.ubahStatusKunjungan(idKunjungan, StatusKunjunganRequestStatus.ditangani)).thenAnswer(
      (_) async => StatusKunjunganResponse.fromJson({
        'id_kunjungan': idKunjungan,
        'status': 'ditangani',
        'waktu_ditangani': '2026-11-02T02:10:00Z',
      }),
    );
    when(() => repo.ubahStatusKunjungan(idKunjungan, StatusKunjunganRequestStatus.selesai)).thenThrow(
      const GalatApi(status: 409, tipe: GalatApi.tipeKonflik, judul: 'Konflik', detail: 'Status tidak bisa diubah.'),
    );
    await bukaHasil(tester, peran: 'dokter', detail: triaseDetail());

    await ketuk(tester, find.widgetWithText(FilledButton, 'Setujui'));
    await tester.tap(find.widgetWithText(FilledButton, 'Setujui').last);
    await tester.pumpAndSettle();
    expect(find.text('Hasil triase disetujui.'), findsOneWidget);

    await ketuk(tester, find.text('Mulai periksa pasien'));
    expect(find.text('Status kunjungan: sedang diperiksa.'), findsOneWidget);
    await ketuk(tester, find.text('Tandai kunjungan selesai'));
    expect(find.text('Status tidak bisa diubah.'), findsOneWidget);
    await tutupAplikasi(tester);
  });

  testWidgets('dokter tanpa status kunjungan tidak melihat tombol status', (tester) async {
    await bukaHasil(
      tester,
      peran: 'dokter',
      detail: triaseDetail(status: 'disetujui'),
      status: null,
    );
    expect(find.text('Mulai periksa pasien'), findsNothing);
    await tutupAplikasi(tester);
  });

  testWidgets('perawat membuka triase ulang, kode QR Eir, dan riwayat dari hasil', (tester) async {
    when(() => repo.tautanEir(idKunjungan)).thenAnswer((_) async => tautanEir());
    when(() => repo.riwayat(idPasien)).thenAnswer((_) async => riwayat());
    await bukaHasil(
      tester,
      detail: triaseDetail(level: 'rendah', status: 'disetujui'),
    );

    await ketuk(tester, find.text('Triase ulang'));
    expect(find.text('Form Triase'), findsOneWidget);
    await kembali(tester);

    await ketuk(tester, find.text('Kode QR Eir untuk pasien'));
    expect(find.text('Kode QR Eir'), findsOneWidget);
    await kembali(tester);

    await ketuk(tester, find.text('Riwayat triase pasien'));
    expect(find.text('Riwayat Triase'), findsOneWidget);
    await tutupAplikasi(tester);
  });

  test('alasan minimal 5 dan maksimal 500 karakter', () {
    expect(periksaAlasan(null), 'Alasan minimal 5 karakter.');
    expect(periksaAlasan('  abc  '), 'Alasan minimal 5 karakter.');
    expect(periksaAlasan('x' * 501), 'Alasan maksimal 500 karakter.');
    expect(periksaAlasan('Cukup jelas'), isNull);
  });
}
