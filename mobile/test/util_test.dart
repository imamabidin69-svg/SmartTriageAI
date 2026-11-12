import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:smarttriage_mobile/api/generated/export.dart';
import 'package:smarttriage_mobile/api/repositori.dart';
import 'package:smarttriage_mobile/router.dart';
import 'package:smarttriage_mobile/rute.dart';
import 'package:smarttriage_mobile/state/antrean.dart';
import 'package:smarttriage_mobile/state/penyedia.dart';
import 'package:smarttriage_mobile/state/sesi.dart';
import 'package:smarttriage_mobile/tema.dart';
import 'package:smarttriage_mobile/util/format.dart';
import 'package:smarttriage_mobile/util/label.dart';
import 'package:smarttriage_mobile/util/validasi.dart';

import 'bantuan/aplikasi.dart';
import 'bantuan/data.dart';

void main() {
  group('format', () {
    final pagiUtc = DateTime.utc(2026, 10, 17, 1, 42);

    test('waktu UTC ditampilkan dalam WIB', () {
      expect(jamWib(pagiUtc), '08.42');
      expect(tanggalWib(pagiUtc), '17 Okt 2026');
      expect(tanggalJamWib(DateTime.utc(2026, 12, 31, 18)), '1 Jan 2027 01.00');
      expect(tanggalSaja(DateTime(1990, 3, 2)), '2 Mar 1990');
      expect(tanggalIso(DateTime(2026, 1, 5)), '2026-01-05');
    });

    test('angka dengan koma desimal', () {
      expect(angka(37.25), '37,3');
      expect(angka(95.0), '95');
      expect(angka(104), '104');
      expect(bacaAngka(' 37,2 '), 37.2);
      expect(bacaAngka(''), isNull);
      expect(bacaAngka('abc'), isNull);
    });

    test('durasi menit', () {
      expect(durasiMenit(12), '12 mnt');
      expect(durasiMenit(60), '1 jam');
      expect(durasiMenit(75), '1 jam 15 mnt');
      // Data simulasi lama bisa menunggu ratusan jam, jadi ditulis dalam hari.
      expect(durasiMenit(24 * 60), '1 hari');
      expect(durasiMenit(26 * 24 * 60 + 16 * 60 + 34), '26 hari 16 jam');
    });
  });

  group('validasi', () {
    test('tanda vital mengikuti batas backend', () {
      expect(periksaTandaVital('nadi', ''), 'Wajib diisi.');
      expect(periksaTandaVital('nadi', 'x'), 'Isi dengan angka.');
      expect(periksaTandaVital('nadi', '80,5'), 'Isi dengan bilangan bulat.');
      expect(periksaTandaVital('saturasi', '101'), 'Harus antara 0 dan 100.');
      expect(periksaTandaVital('suhu', '19,9'), 'Harus antara 20 dan 45.');
      expect(periksaTandaVital('suhu', '37,2'), isNull);
      expect(periksaTandaVital('td_sistolik', '320'), isNull);
    });

    test('hasil lab dan nomor bed', () {
      expect(periksaLab('laktat', ''), isNull);
      expect(periksaLab('laktat', '3,4'), isNull);
      expect(periksaLab('laktat', 'x'), 'Isi dengan angka.');
      expect(periksaLab('laktat', '31'), 'Harus antara 0 dan 30.');
      expect(periksaLab('trombosit', '140.5'), 'Isi dengan bilangan bulat.');
      expect(periksaLab('kreatinin', '1,25'), isNull);
      expect(periksaNomorBed(''), 'Nomor bed wajib diisi.');
      expect(periksaNomorBed('ICU-3'), isNull);
      expect(periksaNomorBed('ICU/3'), 'Hanya huruf, angka, spasi, dan tanda hubung.');
      expect(periksaNomorBed('ICU-1234567'), 'Nomor bed maksimal 10 karakter.');
      expect(persenPeluang(0.6512), '65%');
    });

    test('panjang teks, NIK, telepon, dan usia', () {
      expect(periksaPanjang('', min: 1, maks: 5, nama: 'Nama'), 'Nama wajib diisi.');
      expect(periksaPanjang('abcdef', min: 1, maks: 5, nama: 'Nama'), 'Nama maksimal 5 karakter.');
      expect(periksaNik(''), isNull);
      expect(periksaNik('12345'), 'NIK harus 16 digit angka.');
      expect(periksaNik('3577010101010001'), isNull);
      expect(periksaTelepon(''), isNull);
      expect(periksaTelepon('+62 812-3456-789'), isNull);
      expect(periksaTelepon('0812'), isNotNull);
      expect(periksaTelepon('1' * 21), isNotNull);
      expect(periksaUsia(''), 'Isi tanggal lahir atau perkiraan usia.');
      expect(periksaUsia('151'), 'Usia 0 sampai 150 tahun.');
      expect(periksaUsia('45'), isNull);
    });
  });

  test('setiap nilai enum punya label', () {
    final semua = <String>[
      ...RiskLevel.values.map(labelLevel),
      ...JenisKelamin.values.map(singkatanKelamin),
      ...JenisKelamin.values.map(labelKelamin),
      ...Peran.values.map(labelPeran),
      ...StatusValidasi.values.map(labelStatusValidasi),
      ...SumberRekomendasi.values.map(labelSumberRekomendasi),
      ...SumberTandaVital.values.map(labelSumberTandaVital),
      ...JenisTriase.values.map(labelJenisTriase),
      ...StatusKunjungan.values.map(labelStatusKunjungan),
      ...TingkatKesadaran.values.map(labelKesadaran),
      ...TingkatKesadaran.values.map(singkatanKesadaran),
      ...JenisAlat.values.map(labelAlat),
      ...ItemPeringatanJenis.values.map(labelJenisPeringatan),
    ];
    expect(semua.every((label) => label.isNotEmpty), isTrue);
    expect(urutanTandaVital.every(labelTandaVital.containsKey), isTrue);
    expect(urutanTandaVital.every(labelPendekTandaVital.containsKey), isTrue);
    expect(urutanTandaVital.every(satuanTandaVital.containsKey), isTrue);
    expect(RiskLevel.values.map(Warna.level).toSet(), hasLength(4));
    expect(temaAplikasi().scaffoldBackgroundColor, Warna.latar);
  });

  group('arahkan', () {
    const sesiMasuk = AsyncData<Object?>('pengguna');

    test('menunggu sesi diperiksa', () {
      expect(arahkan(const AsyncLoading(), null, Rute.antrean), Rute.mulai);
      expect(arahkan(const AsyncLoading(), null, Rute.mulai), isNull);
      expect(arahkan(AsyncError<Object?>(Exception('x'), StackTrace.empty), null, Rute.mulai), isNull);
    });

    test('belum masuk ke halaman Masuk', () {
      expect(arahkan(const AsyncData(null), null, Rute.antrean), Rute.masuk);
      expect(arahkan(const AsyncData(null), null, Rute.masuk), isNull);
    });

    test('sudah masuk tidak kembali ke login, dokter tidak membuka Triase Baru', () {
      expect(arahkan(sesiMasuk, Peran.perawat, Rute.masuk), Rute.antrean);
      expect(arahkan(sesiMasuk, Peran.perawat, Rute.triaseBaru), isNull);
      expect(arahkan(sesiMasuk, Peran.dokter, Rute.triaseBaru), Rute.antrean);
      expect(arahkan(sesiMasuk, Peran.dokter, Rute.hasil('x')), isNull);
    });
  });

  group('state', () {
    TestWidgetsFlutterBinding.ensureInitialized();
    setUpAll(daftarkanNilaiCadangan);

    test('penyedia bawaan membuat repository sungguhan', () {
      FlutterSecureStorage.setMockInitialValues({});
      final container = ProviderContainer();
      addTearDown(container.dispose);
      expect(container.read(repositoriProvider), isA<RepositoriApi>());
      expect(container.read(pengambilFotoProvider), isNotNull);
    });

    test('sesi berakhir dari klien HTTP mengosongkan pengguna', () async {
      final repo = RepoTiruan();
      when(repo.adaSesiTersimpan).thenAnswer((_) async => true);
      when(repo.saya).thenAnswer((_) async => pengguna('perawat'));
      final container = ProviderContainer(overrides: [repositoriProvider.overrideWithValue(repo)]);
      addTearDown(container.dispose);
      expect((await container.read(sesiProvider.future))!.peran, Peran.perawat);
      expect(container.read(peranProvider), Peran.perawat);
      container.read(sesiProvider.notifier).berakhir();
      expect(container.read(penggunaProvider), isNull);
      // Dipanggil lagi saat sudah keluar tidak mengubah apa pun.
      container.read(sesiProvider.notifier).berakhir();
      expect(container.read(sesiProvider).value, isNull);
    });

    test('antrean: muat ulang ganda diabaikan, jeda dan lanjut', () async {
      final repo = RepoTiruan();
      aturAntrean(repo);
      final container = ProviderContainer(overrides: [repositoriProvider.overrideWithValue(repo)]);
      addTearDown(container.dispose);
      final langganan = container.listen(antreanProvider, (_, _) {});
      addTearDown(langganan.close);
      await container.read(antreanProvider.future);
      final notifier = container.read(antreanProvider.notifier);
      await Future.wait([notifier.muatUlang(), notifier.muatUlang()]);
      verify(repo.daftarTunggu).called(2);
      notifier
        ..jeda()
        ..jeda()
        ..lanjut();
      await Future<void>.delayed(Duration.zero);
      notifier.lanjut();
      verify(repo.daftarTunggu).called(1);
    });
  });
}
