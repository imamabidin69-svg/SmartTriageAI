import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../api/generated/models/peran.dart';
import '../komponen/peringatan.dart';
import '../state/antrean.dart';
import '../state/sesi.dart';
import '../tema.dart';
import '../util/label.dart';

/// Kerangka halaman utama dengan navigasi bawah seperti mockup Gambar 7.1. Tab Triase Baru hanya untuk perawat,
/// karena registrasi dan input triase memang hanya boleh dilakukan perawat.
class KerangkaUtama extends ConsumerStatefulWidget {
  const KerangkaUtama({super.key, required this.navigasi});

  final StatefulNavigationShell navigasi;

  @override
  ConsumerState<KerangkaUtama> createState() => _KerangkaUtamaState();
}

class _KerangkaUtamaState extends ConsumerState<KerangkaUtama> {
  late final AppLifecycleListener _siklus;

  @override
  void initState() {
    super.initState();
    // Selama aplikasi di latar belakang, daftar tunggu tidak dimuat ulang supaya tidak menghabiskan kuota.
    _siklus = AppLifecycleListener(
      onHide: () => ref.read(antreanProvider.notifier).jeda(),
      onShow: () => ref.read(antreanProvider.notifier).lanjut(),
    );
  }

  @override
  void dispose() {
    _siklus.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // Toast untuk peringatan yang baru muncul (FR-07, TC-12). Mendengarkan provider ini juga menjaga
    // daftar tunggu tetap dimuat ulang walau tab lain yang sedang dibuka.
    ref.listen<AsyncValue<DataAntrean>>(antreanProvider, (_, berikut) {
      final baru = berikut.value?.peringatanBaru ?? const [];
      if (baru.isEmpty) return;
      final pertama = baru.first;
      ScaffoldMessenger.of(context)
        ..hideCurrentSnackBar()
        ..showSnackBar(
          SnackBar(
            backgroundColor: Warna.galat,
            duration: const Duration(seconds: 8),
            content: Text(
              baru.length == 1
                  ? '${labelJenisPeringatan(pertama.jenis)}: ${pertama.pasien.nama}. ${pertama.alasan}'
                  : '${baru.length} peringatan baru, salah satunya ${pertama.pasien.nama}.',
            ),
            action: SnackBarAction(
              label: 'Lihat',
              textColor: Colors.white,
              onPressed: () => bukaPeringatan(context, pertama),
            ),
          ),
        );
    });

    final perawat = ref.watch(peranProvider) == Peran.perawat;
    // Indeks cabang router: 0 daftar tunggu, 1 triase baru, 2 riwayat, 3 profil.
    final cabang = perawat ? const [0, 1, 2, 3] : const [0, 2, 3];
    final terpilih = cabang.indexOf(widget.navigasi.currentIndex);
    return Scaffold(
      body: widget.navigasi,
      bottomNavigationBar: NavigationBar(
        selectedIndex: terpilih < 0 ? 0 : terpilih,
        onDestinationSelected: (i) =>
            widget.navigasi.goBranch(cabang[i], initialLocation: cabang[i] == widget.navigasi.currentIndex),
        destinations: [
          const NavigationDestination(icon: Icon(Icons.format_list_bulleted), label: 'Daftar Tunggu'),
          if (perawat) const NavigationDestination(icon: Icon(Icons.person_add_alt), label: 'Triase Baru'),
          const NavigationDestination(icon: Icon(Icons.history), label: 'Riwayat'),
          const NavigationDestination(icon: Icon(Icons.account_circle_outlined), label: 'Profil'),
        ],
      ),
    );
  }
}
