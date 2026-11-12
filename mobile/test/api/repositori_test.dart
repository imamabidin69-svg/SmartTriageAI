import 'dart:convert';
import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smarttriage_mobile/api/galat_api.dart';
import 'package:smarttriage_mobile/api/generated/export.dart';
import 'package:smarttriage_mobile/api/klien_http.dart';
import 'package:smarttriage_mobile/api/penyimpanan_token.dart';
import 'package:smarttriage_mobile/api/repositori.dart';

import '../bantuan/data.dart';
import '../bantuan/http.dart';

void main() {
  late PenyimpananTokenMemori token;
  late AdapterPalsu adapter;
  late Map<String, Object?> Function(RequestOptions) jawaban;
  late RepositoriApi repo;

  setUp(() {
    token = PenyimpananTokenMemori(const TokenSesi(akses: 'akses', refresh: 'refresh'));
    jawaban = (_) => {};
    adapter = AdapterPalsu((opsi) async => jawabanJson(200, jawaban(opsi)));
    repo = RepositoriApi(KlienHttp(alamat: 'http://server', token: token, saatSesiBerakhir: () {}, adapter: adapter));
  });

  RequestOptions terakhir() => adapter.permintaan.last;

  test('masuk sebagai klien mobile lalu menyimpan token', () async {
    await token.hapus();
    jawaban = (_) => {
      'pengguna': jsonPengguna('perawat'),
      'access_token': 'akses-baru',
      'refresh_token': 'refresh-baru',
      'token_type': 'Bearer',
      'expires_in': 900,
    };
    final pengguna = await repo.masuk('perawat@smarttriage.demo', 'rahasia');
    expect(pengguna.peran, Peran.perawat);
    expect(terakhir().path, '/api/v1/auth/login');
    // Dio mengirim nilai header lewat toString(), dan enum hasil generate mengembalikan nilai JSON-nya.
    expect(terakhir().headers['X-Client'].toString(), 'mobile');
    expect(terakhir().data, {'email': 'perawat@smarttriage.demo', 'password': 'rahasia'});
    expect((await token.baca())!.refresh, 'refresh-baru');
    expect(await repo.adaSesiTersimpan(), isTrue);
  });

  test('jawaban login tanpa token ditolak', () async {
    jawaban = (_) => {'pengguna': jsonPengguna('perawat')};
    await expectLater(
      repo.masuk('a@b.c', 'x'),
      throwsA(isA<GalatApi>().having((g) => g.pesan, 'pesan', 'Server tidak mengirim token. Coba lagi.')),
    );
  });

  test('error HTTP diubah menjadi GalatApi dengan pesan per field', () async {
    adapter = AdapterPalsu(
      (_) async => jawabanJson(422, {
        'type': 'urn:smarttriage:problem:validasi',
        'title': 'Data tidak valid',
        'status': 422,
        'errors': [
          {'field': 'email', 'pesan': 'Format email tidak valid.'},
        ],
      }),
    );
    repo = RepositoriApi(KlienHttp(alamat: 'http://server', token: token, saatSesiBerakhir: () {}, adapter: adapter));
    await expectLater(
      repo.masuk('x', 'y'),
      throwsA(isA<GalatApi>().having((g) => g.field('email'), 'email', 'Format email tidak valid.')),
    );
  });

  test('profil, ganti password, keluar, dan hapus sesi', () async {
    jawaban = (_) => jsonPengguna('dokter');
    expect((await repo.saya()).nama, 'dr. Bagus Kurniawan');
    expect(terakhir().path, '/api/v1/auth/me');

    jawaban = (_) => {};
    await repo.gantiPassword(lama: 'lama12345', baru: 'baru12345');
    expect(terakhir().method, 'PATCH');
    expect(terakhir().data, {'password_lama': 'lama12345', 'password_baru': 'baru12345'});

    await repo.keluar();
    expect(terakhir().path, '/api/v1/auth/logout');
    expect(await repo.adaSesiTersimpan(), isFalse);

    await token.simpan(const TokenSesi(akses: 'a', refresh: 'r'));
    await repo.hapusSesi();
    expect(await repo.adaSesiTersimpan(), isFalse);
  });

  test('daftar tunggu dan peringatan', () async {
    jawaban = (opsi) => opsi.path.endsWith('daftar-tunggu')
        ? {
            'items': [jsonItemTunggu(eirSiap: true)],
            'waktu_server': '2026-11-02T02:00:00Z',
          }
        : {
            'items': [peringatan().toJson()],
          };
    final daftar = await repo.daftarTunggu();
    expect(daftar.items.single.ringkasanEirSiap, isTrue);
    expect(daftar.items.single.statusTanda, ItemDaftarTungguStatusTanda.observasiTerlambat);
    expect(daftar.items.single.nomorBed, 'ICU-2');
    final items = await repo.peringatan();
    expect(items.single.jenis, ItemPeringatanJenis.menungguPersetujuan);
    expect(terakhir().path, '/api/v1/peringatan');
  });

  test('pasien dan kunjungan', () async {
    jawaban = (_) => {
      'items': [pasienRingkas().toJson()],
    };
    expect((await repo.cariPasien('budi')).single.nama, 'Budi Santoso');
    expect(terakhir().queryParameters, {'q': 'budi'});

    jawaban = (_) => kunjunganDibuat().toJson();
    final data = RegistrasiRequest(
      idPasien: null,
      nama: 'Sri',
      tanggalLahir: DateTime(1990, 5, 1),
      perkiraanUsia: null,
      jenisKelamin: JenisKelamin.perempuan,
      nik: null,
      noTelepon: null,
      nomorBed: 'ICU-2',
      asalRuangan: RegistrasiRequestAsalRuangan.igd,
      diagnosisMasuk: 'Syok sepsis',
    );
    expect((await repo.registrasi(data)).nomorBed, 'ICU-2');
    expect((terakhir().data as Map)['asal_ruangan'], 'IGD');
    expect(terakhir().path, '/api/v1/kunjungan');

    jawaban = (_) => {'id_kunjungan': idKunjungan, 'status': 'ditangani', 'waktu_ditangani': null};
    final status = await repo.ubahStatusKunjungan(idKunjungan, StatusKunjunganRequestStatus.ditangani);
    expect(status.status, StatusKunjungan.ditangani);
    expect(terakhir().path, '/api/v1/kunjungan/$idKunjungan/status');
    expect(terakhir().method, 'PATCH');

    jawaban = (_) => tautanEir().toJson();
    expect((await repo.tautanEir(idKunjungan)).url, contains('/eir#t='));
    expect(terakhir().path, '/api/v1/kunjungan/$idKunjungan/tautan-eir');

    jawaban = (_) => ringkasanEir().toJson();
    expect((await repo.ringkasanEir(idKunjungan)).ringkasan!.alergi, 'Alergi amoxicillin');
  });

  test('triase, validasi, riwayat, dan pemindaian', () async {
    jawaban = (_) => jsonTriaseDetail();
    const input = TriaseInput(
      tingkatKesadaran: TingkatKesadaran.a,
      oksigenTambahan: true,
      catatan: null,
      lab: HasilLab(laktat: 3.4, kreatinin: null, trombosit: null, leukosit: null, bilirubin: null),
      tandaVital: TandaVital(tdSistolik: 158, tdDiastolik: 96, nadi: 104, lajuNapas: 22, suhu: 37.2, saturasi: 95),
      idPemindaian: [],
    );
    expect((await repo.buatTriase(idKunjungan, input)).riskLevel, RiskLevel.tinggi);
    expect(terakhir().path, '/api/v1/kunjungan/$idKunjungan/triase');
    final kirim = jsonDecode(jsonEncode(terakhir().data)) as Map;
    expect((kirim['oksigen_tambahan'], (kirim['lab'] as Map)['laktat']), (true, 3.4));
    expect((await repo.detailTriase(idTriase)).penjelasanAi.faktor, hasLength(3));
    expect(terakhir().path, '/api/v1/triase/$idTriase');
    await repo.validasi(
      idTriase,
      const ValidasiRequest(aksi: ValidasiRequestAksi.setujui, riskLevel: null, alasan: null),
    );
    expect(terakhir().path, '/api/v1/triase/$idTriase/validasi');

    jawaban = (_) => riwayat(kursor: 'k2').toJson();
    expect((await repo.riwayat(idPasien, kursor: 'k1')).kursorBerikutnya, 'k2');
    expect(terakhir().queryParameters, {'ukuran': 20, 'kursor': 'k1'});

    jawaban = (_) => hasilPemindaian().toJson();
    final foto = File('${Directory.systemTemp.createTempSync('pindai').path}/layar.jpg')
      ..writeAsBytesSync([0xFF, 0xD8]);
    final hasil = await repo.pindai(JenisAlat.oksimeter, foto);
    expect(hasil.nilai['td_sistolik'], 158);
    final form = terakhir().data as FormData;
    expect((form.fields.single.key, form.fields.single.value), ('jenis_alat', 'oksimeter'));
    expect(form.files.single.key, 'berkas');
  });
}
