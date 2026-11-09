// Uji kontrak dengan backend Flask yang sedang berjalan, memakai repository dan klien hasil generate yang asli.
// Tidak ikut `flutter test` biasa. Jalankan manual setelah backend menyala dan `flask seed-demo` dijalankan:
//
//   flutter test test_backend --dart-define=API_UJI=http://127.0.0.1:5000 \
//     --dart-define=PASSWORD_PERAWAT=... --dart-define=PASSWORD_DOKTER=...
@Tags(['backend'])
library;

import 'dart:io';
import 'dart:math';

import 'package:flutter_test/flutter_test.dart';
import 'package:smarttriage_mobile/api/galat_api.dart';
import 'package:smarttriage_mobile/api/generated/export.dart';
import 'package:smarttriage_mobile/api/klien_http.dart';
import 'package:smarttriage_mobile/api/penyimpanan_token.dart';
import 'package:smarttriage_mobile/api/repositori.dart';

const alamat = String.fromEnvironment('API_UJI');
const passwordPerawat = String.fromEnvironment('PASSWORD_PERAWAT');
const passwordDokter = String.fromEnvironment('PASSWORD_DOKTER');

/// PNG 1x1 piksel, cukup untuk lolos pemeriksaan jenis berkas di server.
const _png = [
  0x89,
  0x50,
  0x4E,
  0x47,
  0x0D,
  0x0A,
  0x1A,
  0x0A,
  0x00,
  0x00,
  0x00,
  0x0D,
  0x49,
  0x48,
  0x44,
  0x52,
  0x00,
  0x00,
  0x00,
  0x01, //
  0x00,
  0x00,
  0x00,
  0x01,
  0x08,
  0x06,
  0x00,
  0x00,
  0x00,
  0x1F,
  0x15,
  0xC4,
  0x89,
  0x00,
  0x00,
  0x00,
  0x0D,
  0x49,
  0x44,
  0x41,
  0x54,
  0x78,
  0x9C,
  0x63,
  0xF8,
  0xCF,
  0xC0,
  0xF0,
  0x1F,
  0x00,
  0x05,
  0x00,
  0x01,
  0xFF,
  0x89,
  0x99,
  0x3D,
  0x1D,
  0x00,
  0x00,
  0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82,
];

(RepositoriApi, KlienHttp) _repo() {
  final klien = KlienHttp(alamat: alamat, token: PenyimpananTokenMemori(), saatSesiBerakhir: () {});
  return (RepositoriApi(klien), klien);
}

void main() {
  test('alur perawat dan dokter terhadap backend sungguhan', () async {
    final (perawat, klienPerawat) = _repo();
    final saya = await perawat.masuk('perawat@smarttriage.demo', passwordPerawat);
    expect(saya.peran, Peran.perawat);
    expect((await perawat.saya()).email, 'perawat@smarttriage.demo');
    expect(await klienPerawat.perbaruiAkses(), isNotNull);

    // Registrasi pasien baru dengan tanggal lahir, lalu dicari lagi.
    final nama = 'Uji Kontrak ${Random().nextInt(1 << 30)}';
    final kunjungan = await perawat.registrasi(
      RegistrasiRequest(
        idPasien: null,
        nama: nama,
        tanggalLahir: DateTime(1990, 5, 17),
        perkiraanUsia: null,
        jenisKelamin: JenisKelamin.perempuan,
        nik: null,
        noTelepon: '0812-3456-7890',
      ),
    );
    expect(kunjungan.status, StatusKunjungan.menunggu);
    final cari = await perawat.cariPasien(nama);
    expect(cari.single.idKunjunganAktif, kunjungan.idKunjungan);
    expect(cari.single.tanggalLahir, DateTime(1990, 5, 17));

    // Pemindaian: bentuk jawaban sama walau model pembaca belum dimuat di server uji.
    final foto = File('${Directory.systemTemp.createTempSync('kontrak').path}/layar.png')..writeAsBytesSync(_png);
    try {
      final pindai = await perawat.pindai(JenisAlat.tensimeter, foto);
      expect(pindai.jenisAlat, JenisAlat.tensimeter);
      expect(pindai.nilai.keys, containsAll(['td_sistolik', 'td_diastolik', 'nadi']));
    } on GalatApi catch (galat) {
      // Foto 1x1 boleh ditolak pembaca yang aktif; yang diuji adalah bentuk Problem Details-nya.
      expect(galat.status, anyOf(422, 503));
    }

    final detail = await perawat.buatTriase(
      kunjungan.idKunjungan,
      const TriaseInput(
        keluhanUtama: 'Demam',
        gejala: 'Demam sejak dua hari disertai pusing',
        kategoriKeluhan: KategoriKeluhan.demam,
        skalaNyeri: 2,
        tingkatKesadaran: TingkatKesadaran.a,
        tandaVital: TandaVital(tdSistolik: 118, tdDiastolik: 76, nadi: 88, lajuNapas: 18, suhu: 38.1, saturasi: 98),
        idPemindaian: [],
      ),
    );
    expect(detail.idKunjungan, kunjungan.idKunjungan);
    expect(detail.riskLevel, isNot(RiskLevel.$unknown));
    expect(detail.penjelasanAi.faktor, isNotEmpty);
    expect(detail.tandaVital.suhu, 38.1);
    expect(detail.statusValidasi, StatusValidasi.menunggu);

    final daftar = await perawat.daftarTunggu();
    final item = daftar.items.firstWhere((i) => i.idKunjungan == kunjungan.idKunjungan);
    expect(item.triaseTerakhir!.idTriase, detail.idTriase);
    expect(item.ringkasanEirSiap, isFalse);
    expect(await perawat.peringatan(), isA<List<ItemPeringatan>>());

    if (detail.riskLevel == RiskLevel.rendah) {
      final tautan = await perawat.tautanEir(kunjungan.idKunjungan);
      expect(tautan.url, contains('/eir#t='));
    } else {
      await expectLater(
        perawat.tautanEir(kunjungan.idKunjungan),
        throwsA(isA<GalatApi>().having((g) => g.status, 'status', 409)),
      );
    }

    // Perawat mengajukan review; alasan pendek ditolak per field.
    await expectLater(
      perawat.validasi(
        detail.idTriase,
        const ValidasiRequest(aksi: ValidasiRequestAksi.ajukanReview, riskLevel: null, alasan: 'abc'),
      ),
      throwsA(isA<GalatApi>().having((g) => g.field('alasan'), 'alasan', isNotNull)),
    );
    final review = await perawat.validasi(
      detail.idTriase,
      const ValidasiRequest(aksi: ValidasiRequestAksi.ajukanReview, riskLevel: null, alasan: 'Mohon dicek dokter'),
    );
    expect(review.statusValidasi, StatusValidasi.menungguReviewDokter);

    // Dokter mengoreksi, lalu memeriksa dan menyelesaikan kunjungan.
    final (dokter, _) = _repo();
    expect((await dokter.masuk('dokter@smarttriage.demo', passwordDokter)).peran, Peran.dokter);
    final levelBaru = detail.riskLevel == RiskLevel.sedang ? RiskLevel.tinggi : RiskLevel.sedang;
    final koreksi = await dokter.validasi(
      detail.idTriase,
      ValidasiRequest(aksi: ValidasiRequestAksi.koreksi, riskLevel: levelBaru, alasan: 'Koreksi uji kontrak'),
    );
    expect((koreksi.statusValidasi, koreksi.riskLevel), (StatusValidasi.dikoreksi, levelBaru));
    expect(koreksi.catatanValidasiTerakhir, 'Koreksi uji kontrak');

    await expectLater(
      dokter.ringkasanEir(kunjungan.idKunjungan),
      throwsA(isA<GalatApi>().having((g) => g.status, 'status', 404)),
    );

    final riwayat = await dokter.riwayat(cari.single.idPasien);
    expect(riwayat.items.single.riskLevel, levelBaru);
    expect(riwayat.pasien.nama, nama);

    expect(
      (await dokter.ubahStatusKunjungan(kunjungan.idKunjungan, StatusKunjunganRequestStatus.ditangani)).status,
      StatusKunjungan.ditangani,
    );
    expect(
      (await dokter.ubahStatusKunjungan(kunjungan.idKunjungan, StatusKunjunganRequestStatus.selesai)).status,
      StatusKunjungan.selesai,
    );

    // Perawat tidak boleh mengubah status kunjungan.
    await expectLater(
      perawat.ubahStatusKunjungan(kunjungan.idKunjungan, StatusKunjunganRequestStatus.selesai),
      throwsA(isA<GalatApi>().having((g) => g.tipe, 'tipe', GalatApi.tipeAksesDitolak)),
    );

    await dokter.keluar();
    expect(await dokter.adaSesiTersimpan(), isFalse);
    await perawat.keluar();
  }, skip: alamat.isEmpty ? 'Isi --dart-define=API_UJI untuk menjalankan uji kontrak.' : false);
}
