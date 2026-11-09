import 'dart:io';

import 'galat_api.dart';
import 'generated/export.dart';
import 'klien_http.dart';
import 'penyimpanan_token.dart';

/// Semua pemanggilan REST API dari halaman lewat kelas ini. Nama method hasil generate mengikuti operationId
/// backend yang panjang, jadi dibungkus di sini, dan setiap error diubah menjadi [GalatApi].
class RepositoriApi {
  RepositoriApi(this._http) : _api = KlienApiDasar(_http.dio);

  final KlienHttp _http;
  final KlienApiDasar _api;

  Future<T> _jalankan<T>(Future<T> Function() aksi) async {
    try {
      return await aksi();
    } catch (galat) {
      throw GalatApi.dari(galat);
    }
  }

  // ------------------------------------------------------------ autentikasi

  Future<bool> adaSesiTersimpan() async => await _http.token.baca() != null;

  /// Login dengan header X-Client: mobile, sehingga token dikirim di body lalu disimpan di penyimpanan aman.
  Future<PenggunaResponse> masuk(String email, String password) async {
    final sesi = await _jalankan(
      () => _api.autentikasi.authLoginLoginPost(
        body: LoginRequest(email: email, password: password),
        xClient: XClient.mobile,
      ),
    );
    final akses = sesi.accessToken;
    final refresh = sesi.refreshToken;
    if (akses == null || refresh == null) {
      throw const GalatApi(status: 500, tipe: 'token-kosong', judul: 'Server tidak mengirim token. Coba lagi.');
    }
    await _http.token.simpan(TokenSesi(akses: akses, refresh: refresh));
    return sesi.pengguna;
  }

  Future<PenggunaResponse> saya() => _jalankan(_api.autentikasi.authMeMeGet);

  Future<void> keluar() => _http.keluar();

  /// Menghapus token tanpa menghubungi server, misalnya bila akun admin mencoba masuk.
  Future<void> hapusSesi() => _http.token.hapus();

  Future<void> gantiPassword({required String lama, required String baru}) => _jalankan(
    () => _api.autentikasi.authGantiPasswordPasswordPatch(
      body: GantiPasswordRequest(passwordLama: lama, passwordBaru: baru),
    ),
  );

  // ------------------------------------------------------------ daftar tunggu dan peringatan

  Future<DaftarTungguResponse> daftarTunggu() => _jalankan(_api.antrean.antreanDaftarTungguDaftarTungguGet);

  Future<List<ItemPeringatan>> peringatan() async =>
      (await _jalankan(_api.antrean.antreanPeringatanPeringatanGet)).items;

  // ------------------------------------------------------------ pasien dan kunjungan

  Future<List<PasienRingkas>> cariPasien(String kata) async =>
      (await _jalankan(() => _api.kunjungan.kunjunganCariPasienPasienGet(q: kata))).items;

  Future<KunjunganDibuatResponse> registrasi(RegistrasiRequest data) =>
      _jalankan(() => _api.kunjungan.kunjunganRegistrasiKunjunganPost(body: data));

  Future<StatusKunjunganResponse> ubahStatusKunjungan(String idKunjungan, StatusKunjunganRequestStatus status) =>
      _jalankan(
        () => _api.kunjungan.kunjunganUbahStatusKunjunganUuidIdKunjunganStatusPatch(
          idKunjungan: idKunjungan,
          body: StatusKunjunganRequest(status: status),
        ),
      );

  Future<TautanEirResponse> tautanEir(String idKunjungan) =>
      _jalankan(() => _api.kunjungan.kunjunganTautanEirKunjunganUuidIdKunjunganTautanEirPost(idKunjungan: idKunjungan));

  Future<RingkasanEirResponse> ringkasanEir(String idKunjungan) => _jalankan(
    () => _api.kunjungan.kunjunganRingkasanEirKunjunganUuidIdKunjunganRingkasanEirGet(idKunjungan: idKunjungan),
  );

  // ------------------------------------------------------------ triase

  Future<TriaseDetail> buatTriase(String idKunjungan, TriaseInput data) => _jalankan(
    () => _api.triase.triaseBuatTriaseKunjunganUuidIdKunjunganTriasePost(idKunjungan: idKunjungan, body: data),
  );

  Future<TriaseDetail> detailTriase(String idTriase) =>
      _jalankan(() => _api.triase.triaseDetailTriaseTriaseUuidIdTriaseGet(idTriase: idTriase));

  Future<TriaseDetail> validasi(String idTriase, ValidasiRequest data) =>
      _jalankan(() => _api.triase.triaseValidasiTriaseTriaseUuidIdTriaseValidasiPost(idTriase: idTriase, body: data));

  Future<RiwayatResponse> riwayat(String idPasien, {String? kursor}) =>
      _jalankan(() => _api.triase.triaseRiwayatPasienPasienUuidIdPasienRiwayatGet(idPasien: idPasien, kursor: kursor));

  /// Mengirim foto layar alat. Foto hanya diproses di memori server lalu dibuang (FR-04).
  Future<HasilPemindaianResponse> pindai(JenisAlat alat, File foto) =>
      _jalankan(() => _api.pemindaian.pemindaianPindaiPemindaianPost(jenisAlat: alat, berkas: foto));
}
