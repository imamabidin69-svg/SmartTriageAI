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
      icon: Badge(isLabelVisible: jumlah > 0, label: Text('$jumlah'), child: const Icon(Icons.notifications_outlined)),
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
              padding: EdgeInsets.fromLTRB(16, 0, 16, 10),
              child: Text('Peringatan', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700)),
            ),
            const Divider(),
            if (daftar.isEmpty)
              const Padding(
                padding: EdgeInsets.fromLTRB(16, 16, 16, 32),
                child: Text('Tidak ada peringatan.', style: TextStyle(color: Warna.teksRedup)),
              )
            else
              Flexible(
                child: ListView.separated(
                  shrinkWrap: true,
                  itemCount: daftar.length,
                  separatorBuilder: (_, _) => const Divider(),
                  itemBuilder: (context, i) {
                    final item = daftar[i];
                    return ListTile(
                      leading: const Icon(Icons.warning_amber_rounded, color: Warna.kritis),
                      title: Text('${item.pasien.nama}: ${labelJenisPeringatan(item.jenis)}'),
                      subtitle: Text('${item.alasan} · ${jamWib(item.waktu)}'),
                      trailing: const Icon(Icons.chevron_right),
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

/// Panel peringatan di atas daftar tunggu: blok putih dengan garis merah di kiri, tiap baris bisa diketuk.
class PanelPeringatan extends StatelessWidget {
  const PanelPeringatan(this.daftar, {super.key});

  final List<ItemPeringatan> daftar;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(
          left: BorderSide(color: Warna.kritis, width: 4),
          top: BorderSide(color: Warna.garis),
          bottom: BorderSide(color: Warna.garis),
        ),
      ),
      padding: const EdgeInsets.only(top: 12, bottom: 6),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Padding(
            padding: EdgeInsets.fromLTRB(12, 0, 16, 4),
            child: Row(
              children: [
                Icon(Icons.warning_amber_rounded, color: Warna.kritis, size: 20),
                SizedBox(width: 8),
                Text(
                  'Peringatan',
                  style: TextStyle(color: Warna.galat, fontWeight: FontWeight.w700, fontSize: 16),
                ),
              ],
            ),
          ),
          for (final item in daftar)
            InkWell(
              onTap: () => bukaPeringatan(context, item),
              child: Padding(
                padding: const EdgeInsets.fromLTRB(12, 8, 8, 8),
                child: Row(
                  children: [
                    Expanded(child: Text('${item.pasien.nama}: ${item.alasan}')),
                    const Icon(Icons.chevron_right, color: Warna.teksSamar),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }
}
