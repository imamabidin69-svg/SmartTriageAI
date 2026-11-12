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
Finder _lab(String kolom) => find.byKey(ValueKey('lab-$kolom'));

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
  await ketuk(tester, find.text('Ya, oksigen'));
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
        nomorBed: 'ICU-2',
        waktuDatang: DateTime.utc(2026, 11, 2, 1, 42),
        triaseUlang: ulang,
        ringkasanEirSiap: eirSiap,
      ),
    );
  }

  testWidgets('isian kosong dan di luar batas ditolak di perangkat', (tester) async {
    await bukaForm(tester);
    expect(find.text('Budi Santoso'), findsOneWidget);
    expect(find.text('Penilaian Awal'), findsOneWidget);
    expect(find.text('Penilaian awal · Bed ICU-2'), findsOneWidget);
    expect(find.text('45 th · Laki-laki · masuk 08.42'), findsOneWidget);

    // Tombol Nilai prioritas menempel di bawah layar, jadi pesan di bawah perlu digulir dulu.
    await ketuk(tester, find.text('Nilai prioritas'));
    expect(find.text('Wajib diisi.'), findsWidgets);
    await gulirSampaiAda(tester, find.text('Pilih tingkat kesadaran.'));
    await gulirSampaiAda(tester, find.text('Pilih apakah pasien mendapat oksigen tambahan.'));

    await gulirKeAtasSampaiAda(tester, _kolom('saturasi'));
    await isi(tester, _kolom('saturasi'), '120');
    await isi(tester, _kolom('nadi'), '7');
    await tester.pump();
    expect(find.text('Harus antara 0 dan 100.'), findsOneWidget);
    await isi(tester, _lab('laktat'), '31');
    await isi(tester, _lab('trombosit'), '2500');
    await tester.pump();
    expect(find.text('Harus antara 0 dan 30.'), findsOneWidget);
    expect(find.text('Harus antara 0 dan 2000.'), findsOneWidget);
    verifyNever(() => repo.buatTriase(any(), any()));
    await tutupAplikasi(tester);
  });

  testWidgets('menilai prioritas lalu membuka Hasil Penilaian', (tester) async {
    when(() => repo.buatTriase(idKunjungan, any())).thenAnswer((_) async => triaseDetail());
    await bukaForm(tester);
    await _isiFormLengkap(tester);
    await isi(tester, _lab('laktat'), '3,4');
    await isi(tester, _lab('kreatinin'), '1,45');
    await isi(tester, _lab('trombosit'), '140');
    await gulirSampaiAda(tester, find.byKey(const ValueKey('vasopresor')));
    await ketuk(tester, find.byKey(const ValueKey('vasopresor')));
    await isi(tester, find.byKey(const ValueKey('catatan')), '  Urin 25 ml/jam ');
    await ketuk(tester, find.text('Nilai prioritas'));

    final input = verify(() => repo.buatTriase(idKunjungan, captureAny())).captured.single as TriaseInput;
    // Dio mengubah objek bersarang lewat jsonEncode, jadi dibandingkan setelah encode.
    expect(jsonDecode(jsonEncode(input.toJson())), {
      'tingkat_kesadaran': 'A',
      'oksigen_tambahan': true,
      'tanda_vital': {
        'td_sistolik': 158,
        'td_diastolik': 96,
        'nadi': 104,
        'laju_napas': 22,
        'suhu': 37.2,
        'saturasi': 95,
      },
      'lab': {'laktat': 3.4, 'kreatinin': 1.45, 'trombosit': 140, 'leukosit': null, 'bilirubin': null},
      'ventilator': false,
      'vasopresor': true,
      'catatan': 'Urin 25 ml/jam',
      'id_pemindaian': <String>[],
    });
    expect(find.text('Hasil Penilaian'), findsOneWidget);
    expect(find.text('Tinggi'), findsOneWidget);
    // Form diganti halaman hasil, jadi kembali langsung ke papan prioritas.
    await kembali(tester);
    expect(find.text('Prioritas Pasien ICU'), findsOneWidget);
    await tutupAplikasi(tester);
  });

  testWidgets('catatan kosong dikirim null dan udara ruangan dikirim false', (tester) async {
    when(() => repo.buatTriase(idKunjungan, any())).thenAnswer((_) async => triaseDetail());
    await bukaForm(tester);
    await _isiFormLengkap(tester);
    await ketuk(tester, find.text('Udara ruangan'));
    await ketuk(tester, find.text('Nilai prioritas'));
    final input = verify(() => repo.buatTriase(idKunjungan, captureAny())).captured.single as TriaseInput;
    expect((input.oksigenTambahan, input.catatan, input.lab!.laktat), (false, null, null));
    await tutupAplikasi(tester);
  });

  testWidgets('pesan per field dari server ditampilkan di kolomnya', (tester) async {
    when(() => repo.buatTriase(any(), any())).thenThrow(
      const GalatApi(
        status: 422,
        tipe: 'urn:smarttriage:problem:validasi',
        judul: 'Data tidak valid',
        pesanField: {'tanda_vital.suhu': 'Suhu harus antara 20 dan 45.', 'lab.laktat': 'Laktat maksimal 30 mmol/L.'},
      ),
    );
    await bukaForm(tester);
    await _isiFormLengkap(tester);
    await ketuk(tester, find.text('Nilai prioritas'));
    expect(find.text('Periksa kembali kolom yang ditandai merah.'), findsOneWidget);
    expect(find.text('Suhu harus antara 20 dan 45.'), findsOneWidget);
    await gulirSampaiAda(tester, find.text('Laktat maksimal 30 mmol/L.'));

    when(() => repo.buatTriase(any(), any())).thenThrow(
      const GalatApi(
        status: 409,
        tipe: GalatApi.tipeKonflik,
        judul: 'Konflik',
        detail: 'Pasien ini sudah keluar dari ICU, jadi observasi tidak bisa ditambahkan.',
      ),
    );
    await ketuk(tester, find.text('Nilai prioritas'));
    expect(find.text('Pasien ini sudah keluar dari ICU, jadi observasi tidak bisa ditambahkan.'), findsOneWidget);
    await tutupAplikasi(tester);
  });

  testWidgets('angka dari foto layar alat mengisi kolom dan ditandai (FR-04, TC-07)', (tester) async {
    final kamera = PengambilFotoUji();
    when(() => repo.pindai(JenisAlat.tensimeter, any())).thenAnswer((_) async => hasilPemindaian());
    when(() => repo.buatTriase(any(), any())).thenAnswer((_) async => triaseDetail());
    await bukaForm(tester, ulang: true, kamera: kamera);
    expect(find.text('Observasi Pasien'), findsOneWidget);

    await ketuk(tester, find.text('Pindai monitor'));
    expect(find.text('Pindai Layar Alat'), findsOneWidget);
    await ketuk(tester, find.text('Ambil foto'));
    expect(find.text('97% yakin'), findsOneWidget);
    expect(find.text('tidak terbaca'), findsOneWidget);
    expect(find.text('Kolom yang tidak terbaca dibiarkan kosong untuk diisi manual.'), findsOneWidget);
    // Foto sementara dihapus setelah dikirim.
    expect(kamera.terakhir!.existsSync(), isFalse);

    await ketuk(tester, find.text('Pakai angka ini'));
    expect(find.text('Observasi Pasien'), findsOneWidget);
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
    await ketuk(tester, find.text('Nilai prioritas'));
    final input = verify(() => repo.buatTriase(idKunjungan, captureAny())).captured.single as TriaseInput;
    expect(input.idPemindaian, [idPemindaian]);
    expect(input.tandaVital.tdSistolik, 158);
    expect(input.tandaVital.tdDiastolik, 90);
    await tutupAplikasi(tester);
  });

  testWidgets('ringkasan Eir keluarga bisa dibaca dari form (TC-15)', (tester) async {
    when(() => repo.ringkasanEir(idKunjungan)).thenAnswer((_) async => ringkasanEir());
    await bukaForm(tester, eirSiap: true);
    expect(find.text('Ringkasan Eir dari keluarga sudah masuk'), findsOneWidget);
    await ketuk(tester, find.text('Baca ringkasan Eir'));
    expect(find.text('Percakapan Eir'), findsOneWidget);
    expect(find.text('Alergi amoxicillin'), findsOneWidget);
    await kembali(tester);
    expect(find.text('Penilaian Awal'), findsOneWidget);
    await tutupAplikasi(tester);
  });

  testWidgets('pemindaian: pembaca tidak tersedia, tidak ada angka, error server, dan kamera gagal', (tester) async {
    final kamera = PengambilFotoUji();
    when(() => repo.pindai(any(), any())).thenAnswer((_) async => hasilPemindaian(tersedia: false));
    await bukaForm(tester, kamera: kamera);
    await ketuk(tester, find.text('Pindai monitor'));

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
