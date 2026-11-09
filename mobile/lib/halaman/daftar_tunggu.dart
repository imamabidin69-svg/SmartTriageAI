import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../api/generated/models/item_daftar_tunggu.dart';
import '../api/generated/models/item_daftar_tunggu_status_tanda.dart';
import '../api/generated/models/peran.dart';
import '../api/generated/models/risk_level.dart';
import '../api/generated/models/status_kunjungan.dart';
import '../komponen/peringatan.dart';
import '../komponen/umum.dart';
import '../rute.dart';
import '../state/antrean.dart';
import '../state/sesi.dart';
import '../tema.dart';
import '../util/format.dart';
import '../util/label.dart';

/// Daftar Tunggu (SKPL Tabel 7.1 no. 2): pasien non-merah yang menunggu dokter, lama menunggu dibanding batas,
/// penanda triase ulang, dan panel peringatan.
class HalamanDaftarTunggu extends ConsumerWidget {
  const HalamanDaftarTunggu({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final antrean = ref.watch(antreanProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Daftar Tunggu IGD'), actions: const [TombolPeringatan()]),
      body: switch (antrean) {
        AsyncData(:final value) => RefreshIndicator(
          onRefresh: () => ref.read(antreanProvider.notifier).muatUlang(),
          child: _IsiDaftar(value),
        ),
        AsyncError(:final error) => TampilanGalat(error, cobaLagi: () => ref.invalidate(antreanProvider)),
        _ => const TampilanMemuat(pesan: 'Memuat daftar tunggu...'),
      },
    );
  }
}

class _IsiDaftar extends ConsumerWidget {
  const _IsiDaftar(this.data);

  final DataAntrean data;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final items = data.daftar.items;
    final galat = data.galatMuatUlang;
    final jumlah = <RiskLevel, int>{};
    var belumDitriase = 0;
    for (final item in items) {
      final level = item.triaseTerakhir?.riskLevel;
      if (level == null) {
        belumDitriase++;
      } else {
        jumlah[level] = (jumlah[level] ?? 0) + 1;
      }
    }
    return ListView(
      padding: const EdgeInsets.all(16),
      physics: const AlwaysScrollableScrollPhysics(),
      children: [
        if (galat != null) ...[
          KotakPesan(
            '${galat.pesan} Daftar di bawah adalah data terakhir yang berhasil dimuat.',
            jenis: JenisPesan.peringatan,
          ),
          const SizedBox(height: 12),
        ],
        if (data.peringatan.isNotEmpty) ...[PanelPeringatan(data.peringatan), const SizedBox(height: 12)],
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            for (final level in const [RiskLevel.kritis, RiskLevel.tinggi, RiskLevel.sedang, RiskLevel.rendah])
              _RingkasanLevel(LencanaRisiko(level), jumlah[level] ?? 0),
            if (belumDitriase > 0)
              _RingkasanLevel(
                const Tanda('Belum ditriase', warna: Warna.peringatan, latar: Warna.peringatanMuda),
                belumDitriase,
              ),
          ],
        ),
        const SizedBox(height: 16),
        if (items.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 48),
            child: Text(
              'Tidak ada pasien yang menunggu dokter.',
              textAlign: TextAlign.center,
              style: TextStyle(color: Warna.teksRedup),
            ),
          )
        else
          for (final item in items) ...[KartuPasienTunggu(item), const SizedBox(height: 12)],
      ],
    );
  }
}

class _RingkasanLevel extends StatelessWidget {
  const _RingkasanLevel(this.label, this.jumlah);

  final Widget label;
  final int jumlah;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(8, 6, 14, 6),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Warna.garis),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          label,
          const SizedBox(width: 8),
          Text('$jumlah', style: const TextStyle(fontSize: 16)),
        ],
      ),
    );
  }
}

/// Satu kartu pasien di daftar tunggu.
class KartuPasienTunggu extends ConsumerWidget {
  const KartuPasienTunggu(this.item, {super.key});

  final ItemDaftarTunggu item;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final peran = ref.watch(peranProvider);
    final triase = item.triaseTerakhir;
    final pasien = item.pasien;
    final kritis = triase?.riskLevel == RiskLevel.kritis;
    final lewat = item.statusTanda == ItemDaftarTungguStatusTanda.perluTriaseUlang;
    final identitas = [
      if (pasien.usia != null) '${pasien.usia} th',
      singkatanKelamin(pasien.jenisKelamin),
      'datang ${jamWib(item.waktuDatang)}',
    ].join(' · ');

    final tanda = <Widget>[
      if (triase == null) const Tanda('Belum ditriase', warna: Warna.peringatan, latar: Warna.peringatanMuda),
      if (lewat) const Tanda('Perlu triase ulang', warna: Color(0xFF92400E), latar: Warna.peringatanMuda),
      if (item.reviewDiajukan)
        const Tanda('Menunggu review dokter', warna: Warna.galat, latar: Warna.galatMuda)
      else if (kritis && item.menungguValidasi)
        const Tanda('Menunggu dokter', warna: Warna.galat, latar: Warna.galatMuda),
      if (item.ringkasanEirSiap) const Tanda('Ringkasan Eir siap', warna: Color(0xFF1D4ED8), latar: Warna.infoMuda),
    ];
    final lama = durasiMenit(item.lamaMenungguMenit);
    final batas = item.batasTungguMenit;
    final teksWaktu = triase == null
        ? '$lama sejak datang'
        : kritis
        ? '$lama · segera'
        : batas == null
        ? lama
        : '$lama / batas $batas';

    final perawat = peran == Peran.perawat;
    final aksi = <Widget>[
      if (perawat && (triase == null || lewat))
        TextButton.icon(
          onPressed: () => _bukaForm(context, ulang: triase != null),
          icon: const Icon(Icons.edit_note),
          label: Text(triase == null ? 'Isi triase' : 'Triase ulang'),
        ),
      if (perawat && triase?.riskLevel == RiskLevel.rendah)
        TextButton.icon(
          onPressed: () => context.push(Rute.kodeQrEir(item.idKunjungan), extra: pasien),
          icon: const Icon(Icons.qr_code_2),
          label: const Text('Kode QR Eir'),
        ),
    ];

    return Card(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
        side: BorderSide(color: kritis ? const Color(0xFFFCA5A5) : Warna.garis, width: kritis ? 1.5 : 1),
      ),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: () => _buka(context, peran),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(pasien.nama, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
                        const SizedBox(height: 2),
                        Text(identitas, style: const TextStyle(color: Warna.teksRedup)),
                      ],
                    ),
                  ),
                  if (triase != null) LencanaRisiko(triase.riskLevel),
                ],
              ),
              if (triase != null) ...[
                const SizedBox(height: 8),
                Text(triase.keluhanUtama, style: const TextStyle(fontSize: 16)),
              ],
              const SizedBox(height: 10),
              Row(
                children: [
                  Expanded(child: Wrap(spacing: 6, runSpacing: 6, children: tanda)),
                  const SizedBox(width: 8),
                  Flexible(
                    child: Text(
                      teksWaktu,
                      textAlign: TextAlign.right,
                      style: TextStyle(
                        color: lewat ? Warna.galat : Warna.teksRedup,
                        fontWeight: lewat ? FontWeight.w600 : FontWeight.normal,
                      ),
                    ),
                  ),
                ],
              ),
              if (aksi.isNotEmpty) ...[const SizedBox(height: 4), Wrap(spacing: 4, children: aksi)],
            ],
          ),
        ),
      ),
    );
  }

  void _bukaForm(BuildContext context, {required bool ulang}) {
    context.push(
      Rute.formTriase(item.idKunjungan),
      extra: InfoFormTriase(
        pasien: item.pasien,
        waktuDatang: item.waktuDatang,
        triaseUlang: ulang,
        ringkasanEirSiap: item.ringkasanEirSiap,
      ),
    );
  }

  void _buka(BuildContext context, Peran? peran) {
    final triase = item.triaseTerakhir;
    if (triase != null) {
      context.push(Rute.hasil(triase.idTriase), extra: const InfoHasil(statusKunjungan: StatusKunjungan.menunggu));
    } else if (peran == Peran.perawat) {
      _bukaForm(context, ulang: false);
    } else {
      tampilkanPesan(context, 'Pasien ini belum ditriase perawat.');
    }
  }
}
