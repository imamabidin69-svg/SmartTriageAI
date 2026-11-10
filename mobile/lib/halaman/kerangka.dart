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
      bottomNavigationBar: NavigasiBawah(
        terpilih: terpilih < 0 ? 0 : terpilih,
        onPilih: (i) => widget.navigasi.goBranch(cabang[i], initialLocation: cabang[i] == widget.navigasi.currentIndex),
        tujuan: [
          const TujuanNavigasi(Icons.format_list_bulleted, 'Daftar Tunggu'),
          if (perawat) const TujuanNavigasi(Icons.person_add_alt, 'Triase Baru'),
          const TujuanNavigasi(Icons.history, 'Riwayat'),
          const TujuanNavigasi(Icons.account_circle_outlined, 'Profil'),
        ],
      ),
    );
  }
}

class TujuanNavigasi {
  const TujuanNavigasi(this.ikon, this.label);

  final IconData ikon;
  final String label;
}

/// Navigasi bawah datar: tab aktif ditandai garis biru di tepi atas dan warna biru, tanpa latar berbentuk pil.
class NavigasiBawah extends StatelessWidget {
  const NavigasiBawah({super.key, required this.tujuan, required this.terpilih, required this.onPilih});

  final List<TujuanNavigasi> tujuan;
  final int terpilih;
  final ValueChanged<int> onPilih;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(top: BorderSide(color: Warna.garis)),
      ),
      child: SafeArea(
        top: false,
        child: SizedBox(
          height: 64,
          child: Row(
            children: [
              for (final (i, t) in tujuan.indexed)
                Expanded(
                  child: _ItemNavigasi(t, aktif: i == terpilih, onTap: () => onPilih(i)),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ItemNavigasi extends StatelessWidget {
  const _ItemNavigasi(this.tujuan, {required this.aktif, required this.onTap});

  final TujuanNavigasi tujuan;
  final bool aktif;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final warna = aktif ? Warna.utama : Warna.teksSamar;
    return Semantics(
      container: true,
      button: true,
      selected: aktif,
      child: InkWell(
        onTap: onTap,
        child: Stack(
          children: [
            if (aktif)
              const Positioned(
                top: 0,
                left: 20,
                right: 20,
                child: SizedBox(
                  height: 3,
                  child: DecoratedBox(
                    decoration: BoxDecoration(
                      color: Warna.utama,
                      borderRadius: BorderRadius.vertical(bottom: Radius.circular(2)),
                    ),
                  ),
                ),
              ),
            Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(tujuan.ikon, color: warna, size: 24),
                  const SizedBox(height: 3),
                  Text(
                    tujuan.label,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(color: warna, fontSize: 12, fontWeight: FontWeight.w700),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
