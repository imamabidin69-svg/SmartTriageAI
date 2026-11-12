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

  Future<void> bukaHasil(WidgetTester tester, {String peran = 'perawat', TriaseDetail? detail}) async {
    final container = await jalankanAplikasi(tester, repo, peran: peran);
    await bukaHalaman(tester, container, Rute.hasil(idTriase), extra: InfoHasil(detail: detail));
  }

  StatusKunjunganResponse statusBaru(String status) => StatusKunjunganResponse.fromJson({
    'id_kunjungan': idKunjungan,
    'status': status,
    'waktu_ditangani': '2026-11-02T02:10:00Z',
  });

  testWidgets('menampilkan level, NEWS2, peluang memburuk, faktor SHAP, dan data observasi (FR-05)', (tester) async {
    when(() => repo.detailTriase(idTriase)).thenAnswer(
      (_) async => triaseDetail(
        levelSebelumnya: 'sedang',
        peringatan: [
          {'field': 'tanda_vital.td_sistolik', 'pesan': 'Tekanan sistolik 158 di atas normal.'},
        ],
      ),
    );
    await bukaHasil(tester);
    expect(find.text('Hasil Penilaian'), findsOneWidget);
    expect(find.text('Bed ICU-2 · Penilaian awal · 2 Nov 2026 08.50'), findsOneWidget);
    expect(find.text('Prioritas penanganan'), findsOneWidget);
    expect(find.text('Tinggi'), findsOneWidget);
    expect(find.text('Naik dari Sedang'), findsOneWidget);
    expect(find.text('NEWS2 6 (tinggi) · peluang memburuk 6 jam 65% (tinggi)'), findsOneWidget);
    expect(find.text('Menunggu persetujuan dokter'), findsOneWidget);
    expect(find.text('Sumber: NEWS2 dan model AI (Random Forest) (rf-icu-physionet2019-v1)'), findsOneWidget);

    await gulirSampaiAda(tester, find.text('Skor NEWS2: 6'));
    expect(find.text('Mendapat oksigen tambahan'), findsOneWidget);
    expect(find.text('+2'), findsNWidgets(2));
    expect(find.text('Level menurut NEWS2: Tinggi'), findsOneWidget);

    await gulirSampaiAda(tester, find.text('Laktat 3,4 mmol/L'));
    expect(find.text('menaikkan peluang memburuk'), findsWidgets);
    expect(find.text('menurunkan peluang memburuk'), findsOneWidget);
    await gulirSampaiAda(tester, find.text('• Tekanan sistolik 158 di atas normal.'));
    // Tanda vital tampil sebagai kisi: angka besar dengan satuan kecil, ditambah status oksigen.
    await gulirSampaiAda(tester, find.text('158/96 mmHg'));
    for (final nilai in ['104 x/mnt', '22 x/mnt', '37,2 °C', '95 %', 'Ya']) {
      expect(find.text(nilai), findsOneWidget, reason: nilai);
    }
    expect(find.text('Sebagian dibaca dari foto'), findsOneWidget);
    await gulirSampaiAda(tester, find.text('Laktat 3,4 mmol/L\nKreatinin 1,45 mg/dL\nTrombosit 140 rb/µL'));
    expect(find.text('Vasopresor'), findsOneWidget);
    await gulirSampaiAda(tester, find.text('Urin 25 ml/jam'));
    await tutupAplikasi(tester);
  });

  testWidgets('tanpa model: NEWS2 saja, tanpa faktor SHAP, lab kosong', (tester) async {
    await bukaHasil(
      tester,
      detail: triaseDetail(
        sumber: 'aturan',
        status: 'disetujui',
        divalidasi: 'dr. Bagus',
        catatan: 'Sesuai',
        lab: false,
      ),
    );
    expect(find.text('Sumber: NEWS2 saja (model tidak tersedia)'), findsOneWidget);
    expect(find.text('NEWS2 6 (tinggi)'), findsOneWidget);
    expect(find.textContaining('dihitung dari skor NEWS2'), findsOneWidget);
    expect(find.text('Faktor yang paling memengaruhi peluang memburuk'), findsNothing);
    await gulirSampaiAda(tester, find.text('Tidak diisi'));
    expect(find.text('Tidak ada'), findsOneWidget);
    await gulirSampaiAda(tester, find.text('Divalidasi oleh'));
    expect(find.text('dr. Bagus'), findsOneWidget);
    expect(find.text('Sesuai'), findsOneWidget);
    // Sudah disetujui: tidak ada tombol validasi lagi.
    expect(find.text('Setujui'), findsNothing);
    await tutupAplikasi(tester);
  });

  testWidgets('observasi tercatat dan level turun', (tester) async {
    await bukaHasil(
      tester,
      detail: triaseDetail(level: 'sedang', status: 'tercatat', jenis: 'ulang', levelSebelumnya: 'tinggi'),
    );
    expect(find.text('Tercatat (level tidak naik)'), findsOneWidget);
    expect(find.text('Turun dari Tinggi'), findsOneWidget);
    expect(find.text('Ajukan review dokter'), findsNothing);
    await tutupAplikasi(tester);
  });

  testWidgets('gagal memuat lalu dicoba lagi', (tester) async {
    var gagal = true;
    when(() => repo.detailTriase(idTriase)).thenAnswer((_) async {
      if (gagal) throw const GalatApi(status: 404, tipe: 'x', judul: 'Observasi tidak ditemukan.');
      return triaseDetail();
    });
    await bukaHasil(tester);
    expect(find.text('Observasi tidak ditemukan.'), findsOneWidget);
    gagal = false;
    await tester.tap(find.text('Coba lagi'));
    await tester.pumpAndSettle();
    expect(find.text('Tinggi'), findsOneWidget);
    await tutupAplikasi(tester);
  });

  testWidgets('perawat tidak bisa menyetujui; ajuan review wajib beralasan', (tester) async {
    when(() => repo.validasi(idTriase, any()))
        .thenAnswer((_) async => triaseDetail(level: 'kritis', status: 'menunggu_review_dokter'));
    await bukaHasil(tester, detail: triaseDetail(level: 'kritis'));
    expect(find.widgetWithText(FilledButton, 'Setujui'), findsNothing);
    await gulirSampaiAda(tester, find.textContaining('Penilaian awal ini perlu disetujui dokter'));

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
    expect(find.text('Review diajukan ke dokter.'), findsWidgets);
    await gulirSampaiAda(tester, find.text('Review sudah diajukan ke dokter.'));
    await tutupAplikasi(tester);
  });

  testWidgets('perawat melihat pesan kenaikan level', (tester) async {
    await bukaHasil(
      tester,
      detail: triaseDetail(jenis: 'ulang', levelSebelumnya: 'sedang'),
    );
    await gulirSampaiAda(tester, find.textContaining('Level pasien naik dan perlu disetujui dokter'));
    await tutupAplikasi(tester);
  });

  testWidgets('dokter menyetujui (TC-10) dan penolakan server ditampilkan', (tester) async {
    var tolak = false;
    when(() => repo.validasi(idTriase, any())).thenAnswer((_) async {
      if (tolak) {
        throw const GalatApi(
          status: 409,
          tipe: GalatApi.tipeKonflik,
          judul: 'Konflik',
          detail: 'Penilaian ini sudah digantikan observasi yang lebih baru.',
        );
      }
      return triaseDetail(status: 'disetujui', divalidasi: 'dr. Bagus Kurniawan');
    });
    await bukaHasil(tester, peran: 'dokter', detail: triaseDetail());
    await ketuk(tester, find.widgetWithText(FilledButton, 'Setujui'));
    expect(find.text('Setujui prioritas pasien?'), findsOneWidget);
    await tester.tap(find.text('Batal'));
    await tester.pumpAndSettle();
    verifyNever(() => repo.validasi(any(), any()));

    tolak = true;
    await ketuk(tester, find.widgetWithText(FilledButton, 'Setujui'));
    await tester.tap(find.widgetWithText(FilledButton, 'Setujui').last);
    await tester.pumpAndSettle();
    expect(find.text('Penilaian ini sudah digantikan observasi yang lebih baru.'), findsOneWidget);

    tolak = false;
    await ketuk(tester, find.widgetWithText(FilledButton, 'Setujui'));
    await tester.tap(find.widgetWithText(FilledButton, 'Setujui').last);
    await tester.pumpAndSettle();
    final data = verify(() => repo.validasi(idTriase, captureAny())).captured.last as ValidasiRequest;
    expect(data.toJson(), {'aksi': 'setujui', 'risk_level': null, 'alasan': null});
    expect(find.text('Prioritas pasien disetujui.'), findsOneWidget);
    await gulirKeAtasSampaiAda(tester, find.text('Disetujui dokter'));
    await tutupAplikasi(tester);
  });

  testWidgets('dokter mengoreksi level dengan alasan (TC-11)', (tester) async {
    when(() => repo.validasi(idTriase, any()))
        .thenAnswer((_) async => triaseDetail(level: 'kritis', status: 'dikoreksi'));
    await bukaHasil(
      tester,
      peran: 'dokter',
      detail: triaseDetail(status: 'menunggu_review_dokter'),
    );
    expect(find.text('Ajukan review dokter'), findsNothing);

    await ketuk(tester, find.text('Koreksi level'));
    expect(find.text('Level saat ini: Tinggi'), findsOneWidget);
    await tester.tap(find.text('Simpan koreksi'));
    await tester.pump();
    expect(find.text('Pilih level hasil koreksi.'), findsOneWidget);
    expect(find.text('Alasan minimal 5 karakter.'), findsOneWidget);

    await tester.tap(find.text('Kritis'));
    await tester.enterText(find.widgetWithText(TextFormField, 'Alasan koreksi'), 'Laktat naik dan MAP turun');
    await tester.tap(find.text('Simpan koreksi'));
    await tester.pumpAndSettle();

    final data = verify(() => repo.validasi(idTriase, captureAny())).captured.single as ValidasiRequest;
    expect(data.toJson(), {'aksi': 'koreksi', 'risk_level': 'kritis', 'alasan': 'Laktat naik dan MAP turun'});
    expect(find.text('Level dikoreksi menjadi kritis.'), findsOneWidget);
    await gulirKeAtasSampaiAda(tester, find.text('Dikoreksi dokter'));
    await tutupAplikasi(tester);
  });

  testWidgets('dokter mengubah status: tindakan, kembali dipantau, dan keluar ICU', (tester) async {
    when(() => repo.ubahStatusKunjungan(idKunjungan, StatusKunjunganRequestStatus.ditangani))
        .thenAnswer((_) async => statusBaru('ditangani'));
    when(() => repo.ubahStatusKunjungan(idKunjungan, StatusKunjunganRequestStatus.menunggu))
        .thenAnswer((_) async => statusBaru('menunggu'));
    when(() => repo.ubahStatusKunjungan(idKunjungan, StatusKunjunganRequestStatus.selesai)).thenThrow(
      const GalatApi(status: 409, tipe: GalatApi.tipeKonflik, judul: 'Konflik', detail: 'Status tidak bisa diubah.'),
    );
    await bukaHasil(
      tester,
      peran: 'dokter',
      detail: triaseDetail(status: 'disetujui'),
    );

    await ketuk(tester, find.text('Mulai tindakan atau operasi'));
    expect(find.text('Status pasien: sedang tindakan.'), findsOneWidget);
    await ketuk(tester, find.text('Selesai tindakan, kembali dipantau'));
    expect(find.text('Status pasien: dirawat.'), findsOneWidget);

    await ketuk(tester, find.text('Pasien keluar ICU'));
    expect(find.text('Tandai pasien keluar ICU?'), findsOneWidget);
    await tester.tap(find.text('Batal'));
    await tester.pumpAndSettle();
    verifyNever(() => repo.ubahStatusKunjungan(idKunjungan, StatusKunjunganRequestStatus.selesai));
    await ketuk(tester, find.text('Pasien keluar ICU'));
    await tester.tap(find.widgetWithText(FilledButton, 'Keluar ICU'));
    await tester.pumpAndSettle();
    expect(find.text('Status tidak bisa diubah.'), findsOneWidget);
    await tutupAplikasi(tester);
  });

  testWidgets('pasien yang sudah keluar ICU tidak punya tombol status dan observasi', (tester) async {
    await bukaHasil(
      tester,
      peran: 'dokter',
      detail: triaseDetail(status: 'disetujui', statusKunjungan: 'selesai'),
    );
    expect(find.text('Mulai tindakan atau operasi'), findsNothing);
    expect(find.text('Pasien keluar ICU'), findsNothing);
    await tutupAplikasi(tester);
  });

  testWidgets('perawat membuka observasi baru, kode QR Eir, dan riwayat dari hasil', (tester) async {
    when(() => repo.tautanEir(idKunjungan)).thenAnswer((_) async => tautanEir());
    when(() => repo.riwayat(idPasien)).thenAnswer((_) async => riwayat());
    await bukaHasil(
      tester,
      detail: triaseDetail(level: 'kritis', status: 'disetujui'),
    );

    await ketuk(tester, find.text('Observasi baru'));
    expect(find.text('Observasi Pasien'), findsOneWidget);
    await kembali(tester);

    await ketuk(tester, find.text('Kode QR Eir untuk keluarga'));
    expect(find.text('Kode QR Eir'), findsOneWidget);
    await kembali(tester);

    await ketuk(tester, find.text('Riwayat observasi pasien'));
    expect(find.text('Riwayat Observasi'), findsOneWidget);
    await tutupAplikasi(tester);
  });

  test('alasan minimal 5 dan maksimal 500 karakter', () {
    expect(periksaAlasan(null), 'Alasan minimal 5 karakter.');
    expect(periksaAlasan('  abc  '), 'Alasan minimal 5 karakter.');
    expect(periksaAlasan('x' * 501), 'Alasan maksimal 500 karakter.');
    expect(periksaAlasan('Cukup jelas'), isNull);
  });
}
