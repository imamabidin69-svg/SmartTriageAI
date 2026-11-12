import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:smarttriage_mobile/api/galat_api.dart';
import 'package:smarttriage_mobile/api/generated/export.dart';

import '../bantuan/aplikasi.dart';
import '../bantuan/data.dart';

void main() {
  late RepoTiruan repo;

  setUpAll(daftarkanNilaiCadangan);
  setUp(() {
    repo = RepoTiruan();
    aturAntrean(repo);
  });

  Future<void> bukaRegistrasi(WidgetTester tester) async {
    await jalankanAplikasi(tester, repo);
    await tester.tap(find.text('Pasien Masuk'));
    await tester.pumpAndSettle();
  }

  testWidgets('mencari pasien lama lalu mendaftarkan kunjungan baru', (tester) async {
    when(() => repo.cariPasien('budi')).thenAnswer((_) async => [pasienRingkas()]);
    when(() => repo.registrasi(any())).thenAnswer((_) async => kunjunganDibuat(baru: false));
    await bukaRegistrasi(tester);

    await tester.enterText(find.byKey(const ValueKey('cari-pasien')), 'b');
    await tester.testTextInput.receiveAction(TextInputAction.search);
    await tester.pumpAndSettle();
    expect(find.text('Ketik minimal 2 huruf nama, atau NIK lengkap.'), findsOneWidget);

    await tester.enterText(find.byKey(const ValueKey('cari-pasien')), 'budi');
    await tester.tap(find.byTooltip('Cari'));
    await tester.pumpAndSettle();
    expect(find.text('45 th · Laki-laki · NIK ••••1234'), findsOneWidget);

    // Bed belum diisi: pasien lama belum bisa dicatat masuk.
    await tester.tap(find.text('Budi Santoso'));
    await tester.pumpAndSettle();
    expect(find.text('Isi nomor bed ICU dulu.'), findsOneWidget);
    verifyNever(() => repo.registrasi(any()));

    await isi(tester, find.byKey(const ValueKey('nomor-bed')), 'ICU-2');
    await ketuk(tester, find.text('Budi Santoso'));
    final data = verify(() => repo.registrasi(captureAny())).captured.single as RegistrasiRequest;
    expect((data.idPasien, data.nomorBed, data.asalRuangan), (idPasien, 'ICU-2', null));
    expect(find.text('Penilaian Awal'), findsOneWidget);
    expect(find.text('Penilaian awal · Bed ICU-2'), findsOneWidget);
    expect(find.text('Budi Santoso'), findsOneWidget);
    await tutupAplikasi(tester);
  });

  testWidgets('pasien tidak ditemukan dan error pencarian', (tester) async {
    when(() => repo.cariPasien('zzz')).thenAnswer((_) async => []);
    when(() => repo.cariPasien('!!')).thenThrow(
      const GalatApi(status: 422, tipe: 'x', judul: 'Data tidak valid', pesanField: {'q': 'Kata kunci tidak valid.'}),
    );
    await bukaRegistrasi(tester);
    await tester.enterText(find.byKey(const ValueKey('cari-pasien')), 'zzz');
    await tester.tap(find.byTooltip('Cari'));
    await tester.pumpAndSettle();
    expect(find.textContaining('Pasien tidak ditemukan'), findsOneWidget);

    await tester.enterText(find.byKey(const ValueKey('cari-pasien')), '!!');
    await tester.tap(find.byTooltip('Cari'));
    await tester.pumpAndSettle();
    expect(find.text('Kata kunci tidak valid.'), findsOneWidget);
    await tutupAplikasi(tester);
  });

  testWidgets('pasien lama yang masih di ICU langsung ke form observasinya', (tester) async {
    when(() => repo.cariPasien('budi')).thenAnswer((_) async => [pasienRingkas(aktif: idKunjungan, nik: null)]);
    await bukaRegistrasi(tester);
    await tester.enterText(find.byKey(const ValueKey('cari-pasien')), 'budi');
    await tester.tap(find.byTooltip('Cari'));
    await tester.pumpAndSettle();
    expect(find.text('45 th · Laki-laki · masih di ICU'), findsOneWidget);

    await tester.tap(find.text('Budi Santoso'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Batal'));
    await tester.pumpAndSettle();
    expect(find.text('Pasien Masuk'), findsWidgets);

    await tester.tap(find.text('Budi Santoso'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Isi observasi'));
    await tester.pumpAndSettle();
    expect(find.text('Observasi Pasien'), findsOneWidget);
    verifyNever(() => repo.registrasi(any()));
    await tutupAplikasi(tester);
  });

  testWidgets('pasien baru: isian diperiksa lalu didaftarkan (FR-02)', (tester) async {
    when(() => repo.registrasi(any())).thenAnswer((_) async => kunjunganDibuat());
    await bukaRegistrasi(tester);

    await ketuk(tester, find.text('Catat masuk ICU dan nilai'));
    await gulirKeAtasSampaiAda(tester, find.text('Nomor bed wajib diisi.'));
    await isi(tester, find.byKey(const ValueKey('nomor-bed')), 'icu 3');
    await ketuk(tester, find.byKey(const ValueKey('asal-ruangan')));
    await tester.tap(find.text('Kamar operasi').last);
    await tester.pumpAndSettle();
    await isi(tester, find.byKey(const ValueKey('diagnosis-masuk')), 'Pasca laparotomi');
    await gulirSampaiAda(tester, find.text('Nama wajib diisi.'));
    expect(find.text('Nama wajib diisi.'), findsOneWidget);
    expect(find.text('Pilih jenis kelamin.'), findsOneWidget);
    expect(find.text('Pilih tanggal lahir.'), findsOneWidget);

    await isi(tester, find.byKey(const ValueKey('nama')), 'Sri Wahyuni');
    await ketuk(tester, find.text('Perempuan'));
    await ketuk(tester, find.text('Tanggal lahir diketahui'));
    await isi(tester, find.byKey(const ValueKey('perkiraan-usia')), '200');
    await isi(tester, find.byKey(const ValueKey('nik')), '123');
    await isi(tester, find.byKey(const ValueKey('telepon')), 'abc');
    await ketuk(tester, find.text('Catat masuk ICU dan nilai'));
    expect(find.text('Usia 0 sampai 150 tahun.'), findsOneWidget);
    expect(find.text('NIK harus 16 digit angka.'), findsOneWidget);
    expect(find.textContaining('Nomor telepon hanya boleh'), findsOneWidget);
    verifyNever(() => repo.registrasi(any()));

    await isi(tester, find.byKey(const ValueKey('perkiraan-usia')), '67');
    await isi(tester, find.byKey(const ValueKey('nik')), '3577010101010001');
    await isi(tester, find.byKey(const ValueKey('telepon')), '0812-3456-789');
    await ketuk(tester, find.text('Catat masuk ICU dan nilai'));

    final data = verify(() => repo.registrasi(captureAny())).captured.single as RegistrasiRequest;
    expect(data.toJson(), {
      'id_pasien': null,
      'nama': 'Sri Wahyuni',
      'tanggal_lahir': null,
      'perkiraan_usia': 67,
      'jenis_kelamin': 'perempuan',
      'nik': '3577010101010001',
      'no_telepon': '0812-3456-789',
      'nomor_bed': 'icu 3',
      'asal_ruangan': 'Kamar operasi',
      'diagnosis_masuk': 'Pasca laparotomi',
    });
    expect(find.text('Penilaian Awal'), findsOneWidget);
    expect(find.text('67 th · Perempuan · masuk 08.42'), findsOneWidget);
    await tutupAplikasi(tester);
  });

  testWidgets('pasien baru dengan tanggal lahir dari kalender', (tester) async {
    when(() => repo.registrasi(any())).thenAnswer((_) async => kunjunganDibuat());
    await bukaRegistrasi(tester);
    await isi(tester, find.byKey(const ValueKey('nomor-bed')), 'ICU-4');
    await isi(tester, find.byKey(const ValueKey('nama')), 'Agus Pratama');
    await ketuk(tester, find.text('Laki-laki'));
    await ketuk(tester, find.text('Pilih tanggal'));
    await tester.tap(find.text('15'));
    await tester.tap(find.text('OKE'));
    await tester.pumpAndSettle();
    await ketuk(tester, find.text('Catat masuk ICU dan nilai'));
    final data = verify(() => repo.registrasi(captureAny())).captured.single as RegistrasiRequest;
    expect(data.tanggalLahir?.day, 15);
    expect(data.perkiraanUsia, isNull);
    await tutupAplikasi(tester);
  });

  testWidgets('pesan server per field dan konflik kunjungan aktif', (tester) async {
    when(() => repo.registrasi(any())).thenThrow(
      const GalatApi(
        status: 409,
        tipe: GalatApi.tipeKonflik,
        judul: 'Konflik',
        detail: 'NIK sudah terdaftar atas pasien lain.',
        pesanField: {'nik': 'NIK sudah terdaftar.'},
      ),
    );
    await bukaRegistrasi(tester);
    await isi(tester, find.byKey(const ValueKey('nomor-bed')), 'ICU-4');
    await isi(tester, find.byKey(const ValueKey('nama')), 'Agus Pratama');
    await ketuk(tester, find.text('Laki-laki'));
    await ketuk(tester, find.text('Tanggal lahir diketahui'));
    await isi(tester, find.byKey(const ValueKey('perkiraan-usia')), '30');
    await isi(tester, find.byKey(const ValueKey('nik')), '3577010101010001');
    await ketuk(tester, find.text('Catat masuk ICU dan nilai'));
    expect(find.text('NIK sudah terdaftar.'), findsOneWidget);

    when(() => repo.registrasi(any())).thenThrow(
      const GalatApi(
        status: 422,
        tipe: 'urn:smarttriage:problem:validasi',
        judul: 'Data tidak valid',
        pesanField: {'nomor_bed': 'Bed ICU-4 masih ditempati pasien lain yang belum keluar ICU.'},
      ),
    );
    await ketuk(tester, find.text('Catat masuk ICU dan nilai'));
    expect(find.text('Bed ICU-4 masih ditempati pasien lain yang belum keluar ICU.'), findsWidgets);
    // Tunggu toast hilang supaya tidak menutupi tombol.
    await tester.pump(const Duration(seconds: 6));
    await tester.pumpAndSettle();

    when(() => repo.registrasi(any())).thenThrow(
      const GalatApi(
        status: 409,
        tipe: GalatApi.tipeKonflik,
        judul: 'Konflik',
        detail: 'Pasien ini masih tercatat dirawat di ICU.',
        ekstra: {'id_kunjungan_aktif': idKunjungan},
      ),
    );
    await ketuk(tester, find.text('Catat masuk ICU dan nilai'));
    expect(find.text('Observasi Pasien'), findsOneWidget);
    await tutupAplikasi(tester);
  });
}
