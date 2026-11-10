import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:smarttriage_mobile/api/galat_api.dart';
import 'package:smarttriage_mobile/api/generated/export.dart';
import 'package:smarttriage_mobile/rute.dart';

import '../bantuan/aplikasi.dart';
import '../bantuan/data.dart';

Finder _kolom(String kolom) => find.byKey(ValueKey('tanda-vital-$kolom'));

Future<void> _isiFormLengkap(WidgetTester tester, {bool tandaVital = true}) async {
  if (tandaVital) {
    const nilai = {
      'td_sistolik': '158',
      'td_diastolik': '96',
      'nadi': '104',
      'saturasi': '95',
      'suhu': '37,2',
      'laju_napas': '22',
    };
    for (final MapEntry(:key, :value) in nilai.entries) {
      await isi(tester, _kolom(key), value);
    }
  }
  await ketuk(tester, find.text('A'));
  await isi(tester, find.byKey(const ValueKey('skala-nyeri')), '7');
  await ketuk(tester, find.byKey(const ValueKey('kategori-keluhan')));
  await tester.tap(find.text('Nyeri dada').last);
  await tester.pumpAndSettle();
  await isi(tester, find.byKey(const ValueKey('keluhan-utama')), 'Nyeri dada kiri menjalar');
  await isi(tester, find.byKey(const ValueKey('gejala')), 'Nyeri dada kiri menjalar ke lengan sejak 1 jam');
}

void main() {
  late RepoTiruan repo;

  setUpAll(daftarkanNilaiCadangan);
  setUp(() {
    repo = RepoTiruan();
    aturAntrean(repo);
  });

  Future<void> bukaForm(
    WidgetTester tester, {
    bool eirSiap = false,
    bool ulang = false,
    PengambilFotoUji? kamera,
  }) async {
    final container = await jalankanAplikasi(tester, repo, kamera: kamera?.ambil);
    await bukaHalaman(
      tester,
      container,
      Rute.formTriase(idKunjungan),
      extra: InfoFormTriase(
        pasien: pasien(),
        waktuDatang: DateTime.utc(2026, 11, 2, 1, 42),
        triaseUlang: ulang,
        ringkasanEirSiap: eirSiap,
      ),
    );
  }

  testWidgets('isian kosong dan di luar batas ditolak di perangkat', (tester) async {
    await bukaForm(tester);
    expect(find.text('Budi Santoso'), findsOneWidget);
    expect(find.text('45 th · Laki-laki · datang 08.42'), findsOneWidget);

    // Tombol Hitung rekomendasi menempel di bawah layar, jadi pesan di blok Keluhan perlu digulir dulu.
    await ketuk(tester, find.text('Hitung rekomendasi'));
    expect(find.text('Wajib diisi.'), findsWidgets);
    expect(find.text('Pilih tingkat kesadaran.'), findsOneWidget);
    await gulirSampaiAda(tester, find.text('Pilih kategori keluhan.'));
    expect(find.text('Pilih kategori keluhan.'), findsOneWidget);

    await isi(tester, _kolom('saturasi'), '120');
    await isi(tester, _kolom('nadi'), '7');
    await tester.pump();
    expect(find.text('Harus antara 0 dan 100.'), findsOneWidget);
    await isi(tester, find.byKey(const ValueKey('gejala')), 'pendek');
    await tester.pump();
    expect(find.text('Gejala minimal 10 karakter.'), findsOneWidget);
    verifyNever(() => repo.buatTriase(any(), any()));
    await tutupAplikasi(tester);
  });

  testWidgets('menghitung rekomendasi lalu membuka Hasil dan Penjelasan', (tester) async {
    when(() => repo.buatTriase(idKunjungan, any())).thenAnswer((_) async => triaseDetail());
    await bukaForm(tester);
    await _isiFormLengkap(tester);
    await ketuk(tester, find.text('Hitung rekomendasi'));

    final input = verify(() => repo.buatTriase(idKunjungan, captureAny())).captured.single as TriaseInput;
    // Dio mengubah objek bersarang lewat jsonEncode, jadi dibandingkan setelah encode.
    expect(jsonDecode(jsonEncode(input.toJson())), {
      'keluhan_utama': 'Nyeri dada kiri menjalar',
      'gejala': 'Nyeri dada kiri menjalar ke lengan sejak 1 jam',
      'kategori_keluhan': 'Nyeri dada',
      'skala_nyeri': 7,
      'tingkat_kesadaran': 'A',
      'tanda_vital': {
        'td_sistolik': 158,
        'td_diastolik': 96,
        'nadi': 104,
        'laju_napas': 22,
        'suhu': 37.2,
        'saturasi': 95,
      },
      'id_pemindaian': <String>[],
    });
    expect(find.text('Hasil Triase'), findsOneWidget);
    expect(find.text('Tinggi'), findsOneWidget);
    // Form diganti halaman hasil, jadi kembali langsung ke daftar tunggu.
    await kembali(tester);
    expect(find.text('Daftar Tunggu IGD'), findsOneWidget);
    await tutupAplikasi(tester);
  });

  testWidgets('pesan per field dari server ditampilkan di kolomnya', (tester) async {
    when(() => repo.buatTriase(any(), any())).thenThrow(
      const GalatApi(
        status: 422,
        tipe: 'urn:smarttriage:problem:validasi',
        judul: 'Data tidak valid',
        pesanField: {'tanda_vital.suhu': 'Suhu harus antara 20 dan 45.', 'gejala': 'Gejala terlalu pendek.'},
      ),
    );
    await bukaForm(tester);
    await _isiFormLengkap(tester);
    await ketuk(tester, find.text('Hitung rekomendasi'));
    expect(find.text('Periksa kembali kolom yang ditandai merah.'), findsOneWidget);
    expect(find.text('Suhu harus antara 20 dan 45.'), findsOneWidget);
    await gulirSampaiAda(tester, find.text('Gejala terlalu pendek.'));
    expect(find.text('Gejala terlalu pendek.'), findsOneWidget);

    when(() => repo.buatTriase(any(), any())).thenThrow(
      const GalatApi(status: 409, tipe: GalatApi.tipeKonflik, judul: 'Konflik', detail: 'Kunjungan sudah selesai.'),
    );
    await ketuk(tester, find.text('Hitung rekomendasi'));
    expect(find.text('Kunjungan sudah selesai.'), findsOneWidget);
    await tutupAplikasi(tester);
  });

  testWidgets('angka dari foto layar alat mengisi kolom dan ditandai (FR-04, TC-07)', (tester) async {
    final kamera = PengambilFotoUji();
    when(() => repo.pindai(JenisAlat.tensimeter, any())).thenAnswer((_) async => hasilPemindaian());
    when(() => repo.buatTriase(any(), any())).thenAnswer((_) async => triaseDetail());
    await bukaForm(tester, ulang: true, kamera: kamera);
    expect(find.text('Triase ulang'), findsOneWidget);

    await ketuk(tester, find.text('Pindai layar alat'));
    expect(find.text('Pindai Layar Alat'), findsOneWidget);
    await ketuk(tester, find.text('Ambil foto'));
    expect(find.text('97% yakin'), findsOneWidget);
    expect(find.text('tidak terbaca'), findsOneWidget);
    expect(find.text('Kolom yang tidak terbaca dibiarkan kosong untuk diisi manual.'), findsOneWidget);
    // Foto sementara dihapus setelah dikirim.
    expect(kamera.terakhir!.existsSync(), isFalse);

    await ketuk(tester, find.text('Pakai angka ini'));
    expect(find.text('Form Triase'), findsOneWidget);
    expect(find.text('2 nilai dibaca dari foto. Periksa sebelum menyimpan.'), findsOneWidget);
    expect(find.text('dari tensimeter'), findsNWidgets(2));

    // Mengubah angka hasil foto menghapus tandanya.
    await isi(tester, _kolom('td_diastolik'), '90');
    expect(find.text('dari tensimeter'), findsOneWidget);

    await isi(tester, _kolom('nadi'), '104');
    await isi(tester, _kolom('saturasi'), '95');
    await isi(tester, _kolom('suhu'), '37');
    await isi(tester, _kolom('laju_napas'), '22');
    await _isiFormLengkap(tester, tandaVital: false);
    await ketuk(tester, find.text('Hitung rekomendasi'));
    final input = verify(() => repo.buatTriase(idKunjungan, captureAny())).captured.single as TriaseInput;
    expect(input.idPemindaian, [idPemindaian]);
    expect(input.tandaVital.tdSistolik, 158);
    expect(input.tandaVital.tdDiastolik, 90);
    await tutupAplikasi(tester);
  });

  testWidgets('isi keluhan dari ringkasan Eir (TC-15)', (tester) async {
    when(() => repo.ringkasanEir(idKunjungan)).thenAnswer((_) async => ringkasanEir());
    await bukaForm(tester, eirSiap: true);
    await ketuk(tester, find.text('Isi dari ringkasan Eir'));
    expect(find.textContaining('dijawab keluarga pasien'), findsOneWidget);
    expect(find.text('Demam tiga hari'), findsOneWidget);
    expect(find.text('Demam naik turun disertai pusing\nSejak: tiga hari lalu'), findsOneWidget);
    expect(find.text('Demam'), findsWidgets);
    await tutupAplikasi(tester);
  });

  testWidgets('ringkasan Eir belum ada atau gagal dimuat', (tester) async {
    when(() => repo.ringkasanEir(idKunjungan))
        .thenAnswer((_) async => ringkasanEir(status: 'berjalan', denganRingkasan: false));
    await bukaForm(tester, eirSiap: true);
    await ketuk(tester, find.text('Isi dari ringkasan Eir'));
    expect(find.text('Percakapan Eir belum selesai, jadi ringkasannya belum ada.'), findsOneWidget);

    when(() => repo.ringkasanEir(idKunjungan)).thenThrow(
      const GalatApi(
        status: 404,
        tipe: 'urn:smarttriage:problem:tidak-ditemukan',
        judul: 'Tidak ditemukan',
        detail: 'Kunjungan ini belum punya sesi Eir.',
      ),
    );
    await ketuk(tester, find.text('Isi dari ringkasan Eir'));
    expect(find.text('Kunjungan ini belum punya sesi Eir.'), findsOneWidget);
    await tutupAplikasi(tester);
  });

  testWidgets('pemindaian: pembaca tidak tersedia, tidak ada angka, error server, dan kamera gagal', (tester) async {
    final kamera = PengambilFotoUji();
    when(() => repo.pindai(any(), any())).thenAnswer((_) async => hasilPemindaian(tersedia: false));
    await bukaForm(tester, kamera: kamera);
    await ketuk(tester, find.text('Pindai layar alat'));

    await ketuk(tester, find.text('Termometer'));
    await ketuk(tester, find.text('Ambil foto'));
    expect(find.text('Pembaca layar belum tersedia di server. Isi tanda vital secara manual.'), findsOneWidget);
    verify(() => repo.pindai(JenisAlat.termometer, any())).called(1);

    when(() => repo.pindai(any(), any())).thenAnswer((_) async => hasilPemindaian(kosongSemua: true));
    await ketuk(tester, find.text('Foto ulang'));
    expect(find.text('Tidak ada angka terbaca'), findsOneWidget);

    when(() => repo.pindai(any(), any())).thenThrow(
      const GalatApi(
        status: 422,
        tipe: 'urn:smarttriage:problem:validasi',
        judul: 'Data tidak valid',
        pesanField: {'berkas': 'Foto harus JPEG atau PNG.'},
      ),
    );
    await ketuk(tester, find.text('Foto ulang'));
    expect(find.text('Foto harus JPEG atau PNG.'), findsOneWidget);

    kamera.gagal = true;
    await ketuk(tester, find.text('Ambil foto'));
    expect(find.textContaining('Kamera tidak bisa dibuka'), findsOneWidget);

    // Pengguna membatalkan kamera: tidak ada yang dikirim.
    kamera
      ..gagal = false
      ..batal = true;
    await ketuk(tester, find.text('Ambil foto'));
    verifyNever(() => repo.pindai(JenisAlat.tensimeter, any()));
    await tutupAplikasi(tester);
  });
}

/// Kamera tiruan: membuat berkas sementara seperti image_picker, atau gagal dan batal sesuai pengaturan.
class PengambilFotoUji {
  bool gagal = false;
  bool batal = false;
  File? terakhir;

  Future<File?> ambil() async {
    if (gagal) throw Exception('kamera tidak tersedia');
    if (batal) return null;
    final berkas = File('${Directory.systemTemp.createTempSync('foto').path}/layar.jpg')
      ..writeAsBytesSync([0xFF, 0xD8, 0xFF]);
    terakhir = berkas;
    return berkas;
  }
}
