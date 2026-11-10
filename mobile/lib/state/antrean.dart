import 'dart:async';
import 'dart:async' as asinkron show AsyncError;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/galat_api.dart';
import '../api/generated/models/daftar_tunggu_response.dart';
import '../api/generated/models/item_peringatan.dart';
import '../konfigurasi.dart';
import 'penyedia.dart';

class DataAntrean {
  const DataAntrean({
    required this.daftar,
    required this.peringatan,
    required this.waktuMuat,
    this.peringatanBaru = const [],
    this.galatMuatUlang,
  });

  final DaftarTungguResponse daftar;
  final List<ItemPeringatan> peringatan;

  /// Kapan data ini terakhir berhasil dimuat, ditampilkan sebagai "Diperbarui" di daftar tunggu.
  final DateTime waktuMuat;

  /// Peringatan yang belum pernah muncul sebelumnya, untuk ditampilkan sebagai toast (FR-07).
  final List<ItemPeringatan> peringatanBaru;

  /// Error saat memuat ulang di latar. Data lama tetap ditampilkan supaya daftar tidak hilang saat sinyal putus.
  final GalatApi? galatMuatUlang;
}

String kunciPeringatan(ItemPeringatan item) =>
    '${item.jenis.json}|${item.idKunjungan}|${item.idTriase ?? ''}|${item.idSesi ?? ''}';

/// Daftar tunggu dan peringatan, dimuat ulang setiap 15 detik selama aplikasi dibuka (Desain 2.7).
class Antrean extends AsyncNotifier<DataAntrean> {
  Timer? _pewaktu;
  Set<String>? _sudahTerlihat;
  bool _memuat = false;

  @override
  Future<DataAntrean> build() async {
    ref.onDispose(() => _pewaktu?.cancel());
    _jalankanPewaktu();
    return _muat();
  }

  void _jalankanPewaktu() {
    _pewaktu?.cancel();
    _pewaktu = Timer.periodic(jedaMuatUlangAntrean, (_) => muatUlang());
  }

  Future<DataAntrean> _muat() async {
    final repo = ref.read(repositoriProvider);
    final DaftarTungguResponse daftar;
    final List<ItemPeringatan> peringatan;
    try {
      (daftar, peringatan) = await (repo.daftarTunggu(), repo.peringatan()).wait;
    } on ParallelWaitError<
      (DaftarTungguResponse?, List<ItemPeringatan>?),
      (asinkron.AsyncError?, asinkron.AsyncError?)
    > catch (galat) {
      // Kedua request dikirim bersamaan; error pertama yang diteruskan ke halaman.
      throw (galat.errors.$1 ?? galat.errors.$2)!.error;
    }
    final kunci = peringatan.map(kunciPeringatan).toSet();
    final lama = _sudahTerlihat;
    // Peringatan yang sudah ada saat aplikasi dibuka tidak dimunculkan sebagai toast, cukup di panel dan badge.
    final baru = lama == null
        ? <ItemPeringatan>[]
        : peringatan.where((p) => !lama.contains(kunciPeringatan(p))).toList();
    _sudahTerlihat = {...?lama, ...kunci};
    return DataAntrean(daftar: daftar, peringatan: peringatan, waktuMuat: DateTime.now(), peringatanBaru: baru);
  }

  /// Memuat ulang tanpa mengosongkan daftar yang sedang tampil.
  Future<void> muatUlang() async {
    if (_memuat) return;
    _memuat = true;
    try {
      final data = await _muat();
      if (ref.mounted) state = AsyncData(data);
    } on GalatApi catch (galat) {
      final lama = state.value;
      if (!ref.mounted) return;
      state = lama == null
          ? AsyncError(galat, StackTrace.current)
          : AsyncData(
              DataAntrean(
                daftar: lama.daftar,
                peringatan: lama.peringatan,
                waktuMuat: lama.waktuMuat,
                galatMuatUlang: galat,
              ),
            );
    } finally {
      _memuat = false;
    }
  }

  /// Aplikasi ke latar belakang: berhenti memanggil server.
  void jeda() {
    _pewaktu?.cancel();
    _pewaktu = null;
  }

  /// Aplikasi kembali dibuka: langsung muat ulang lalu lanjutkan jadwal 15 detik.
  void lanjut() {
    if (_pewaktu != null) return;
    _jalankanPewaktu();
    muatUlang();
  }
}

final antreanProvider = AsyncNotifierProvider.autoDispose<Antrean, DataAntrean>(Antrean.new);
