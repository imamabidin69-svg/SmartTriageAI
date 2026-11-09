import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/galat_api.dart';
import '../api/generated/models/pengguna_response.dart';
import '../api/generated/models/peran.dart';
import 'penyedia.dart';

const pesanBukanStafMedis =
    'Akun admin memakai aplikasi web SmartTriage AI. Aplikasi Android ini khusus perawat dan dokter.';

/// Pengguna yang sedang masuk, atau null bila belum login. Akun admin ditolak karena admin memakai aplikasi
/// web (SKPL bagian 1.2, kebalikan dari keputusan W4 di web).
class Sesi extends AsyncNotifier<PenggunaResponse?> {
  @override
  Future<PenggunaResponse?> build() async {
    final repo = ref.read(repositoriProvider);
    if (!await repo.adaSesiTersimpan()) return null;
    try {
      final pengguna = await repo.saya();
      if (pengguna.peran != Peran.perawat && pengguna.peran != Peran.dokter) {
        await repo.hapusSesi();
        return null;
      }
      return pengguna;
    } on GalatApi catch (galat) {
      // Token tidak berlaku lagi (refresh juga ditolak atau akun dinonaktifkan): kembali ke halaman login.
      if (galat.status == 401 || galat.status == 403) {
        await repo.hapusSesi();
        return null;
      }
      rethrow;
    }
  }

  Future<void> masuk(String email, String password) async {
    final repo = ref.read(repositoriProvider);
    final pengguna = await repo.masuk(email, password);
    if (pengguna.peran != Peran.perawat && pengguna.peran != Peran.dokter) {
      await repo.keluar();
      throw const GalatApi(status: 403, tipe: GalatApi.tipeAksesDitolak, judul: pesanBukanStafMedis);
    }
    state = AsyncData(pengguna);
  }

  Future<void> keluar() async {
    await ref.read(repositoriProvider).keluar();
    state = const AsyncData(null);
  }

  /// Dipanggil klien HTTP bila refresh token ditolak. Token sudah dihapus di sana.
  void berakhir() {
    if (state.value != null) state = const AsyncData(null);
  }

  /// Mencoba lagi setelah gagal menghubungi server saat aplikasi dibuka.
  void cobaLagi() => ref.invalidateSelf();
}

final sesiProvider = AsyncNotifierProvider<Sesi, PenggunaResponse?>(Sesi.new);

/// Pengguna yang sedang masuk. Bisa null sesaat ketika keluar, sebelum router berpindah ke halaman login.
final penggunaProvider = Provider<PenggunaResponse?>((ref) => ref.watch(sesiProvider).value);

/// Peran pengguna yang sedang masuk, atau null bila belum masuk.
final peranProvider = Provider<Peran?>((ref) => ref.watch(penggunaProvider)?.peran);
