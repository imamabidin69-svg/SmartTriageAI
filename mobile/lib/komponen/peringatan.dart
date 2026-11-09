import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../api/generated/models/item_peringatan.dart';
import '../api/generated/models/item_peringatan_jenis.dart';
import '../api/generated/models/status_kunjungan.dart';
import '../rute.dart';
import '../state/antrean.dart';
import '../tema.dart';
import '../util/format.dart';
import '../util/label.dart';

/// Membuka halaman yang relevan untuk satu peringatan: hasil triase, atau percakapan Eir untuk tanda bahaya.
void bukaPeringatan(BuildContext context, ItemPeringatan item) {
  final idTriase = item.idTriase;
  if (item.jenis == ItemPeringatanJenis.tandaBahayaEir || idTriase == null) {
    context.push(Rute.ringkasanEir(item.idKunjungan), extra: item.pasien.nama);
  } else {
    context.push(Rute.hasil(idTriase), extra: const InfoHasil(statusKunjungan: StatusKunjungan.menunggu));
  }
}

/// Tombol lonceng dengan badge jumlah peringatan di kepala halaman (FR-07).
class TombolPeringatan extends ConsumerWidget {
  const TombolPeringatan({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final jumlah = ref.watch(antreanProvider.select((data) => data.value?.peringatan.length ?? 0));
    return IconButton(
      tooltip: jumlah == 0 ? 'Peringatan' : '$jumlah peringatan',
      onPressed: () => showModalBottomSheet<void>(
        context: context,
        isScrollControlled: true,
        showDragHandle: true,
        builder: (_) => const LembarPeringatan(),
      ),
      icon: Badge(
        isLabelVisible: jumlah > 0,
        backgroundColor: Warna.galat,
        label: Text('$jumlah'),
        child: const Icon(Icons.notifications_outlined),
      ),
    );
  }
}

class LembarPeringatan extends ConsumerWidget {
  const LembarPeringatan({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final daftar = ref.watch(antreanProvider.select((data) => data.value?.peringatan ?? const <ItemPeringatan>[]));
    return SafeArea(
      child: ConstrainedBox(
        constraints: BoxConstraints(maxHeight: MediaQuery.sizeOf(context).height * 0.7),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Padding(
              padding: EdgeInsets.fromLTRB(20, 0, 20, 8),
              child: Text('Peringatan', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700)),
            ),
            if (daftar.isEmpty)
              const Padding(
                padding: EdgeInsets.fromLTRB(20, 8, 20, 32),
                child: Text('Tidak ada peringatan.', style: TextStyle(color: Warna.teksRedup)),
              )
            else
              Flexible(
                child: ListView.separated(
                  shrinkWrap: true,
                  itemCount: daftar.length,
                  separatorBuilder: (_, _) => const Divider(height: 1),
                  itemBuilder: (context, i) {
                    final item = daftar[i];
                    return ListTile(
                      leading: const Icon(Icons.warning_amber_rounded, color: Warna.galat),
                      title: Text('${item.pasien.nama}: ${labelJenisPeringatan(item.jenis)}'),
                      subtitle: Text('${item.alasan} · ${jamWib(item.waktu)}'),
                      onTap: () {
                        Navigator.of(context).pop();
                        bukaPeringatan(context, item);
                      },
                    );
                  },
                ),
              ),
          ],
        ),
      ),
    );
  }
}

/// Panel merah di atas daftar tunggu, seperti di mockup Gambar 7.1.
class PanelPeringatan extends StatelessWidget {
  const PanelPeringatan(this.daftar, {super.key});

  final List<ItemPeringatan> daftar;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Warna.galatMuda,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFFFCA5A5)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Peringatan',
            style: TextStyle(color: Color(0xFF991B1B), fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 4),
          for (final item in daftar)
            InkWell(
              onTap: () => bukaPeringatan(context, item),
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 3),
                child: Text('${item.pasien.nama}: ${item.alasan}', style: const TextStyle(color: Warna.galat)),
              ),
            ),
        ],
      ),
    );
  }
}
