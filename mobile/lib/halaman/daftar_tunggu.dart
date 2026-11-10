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
/// penanda triase ulang, dan panel peringatan. Tampilannya rapat seperti papan pantau pasien di IGD.
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

class _IsiDaftar extends StatelessWidget {
  const _IsiDaftar(this.data);

  final DataAntrean data;

  @override
  Widget build(BuildContext context) {
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
      padding: const EdgeInsets.only(bottom: 24),
      physics: const AlwaysScrollableScrollPhysics(),
      children: [
        _Sensus(jumlah: jumlah, belumDitriase: belumDitriase),
        _BarisKeterangan(jumlahPasien: items.length, waktuMuat: data.waktuMuat),
        if (galat != null)
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
            child: KotakPesan(
              '${galat.pesan} Daftar di bawah adalah data terakhir yang berhasil dimuat.',
              jenis: JenisPesan.peringatan,
            ),
          ),
        if (data.peringatan.isNotEmpty) ...[PanelPeringatan(data.peringatan), const SizedBox(height: 12)],
        if (items.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 48, horizontal: 16),
            child: Text(
              'Tidak ada pasien yang menunggu dokter.',
              textAlign: TextAlign.center,
              style: TextStyle(color: Warna.teksRedup),
            ),
          )
        else ...[
          const Divider(),
          for (final item in items) BarisPasienTunggu(item),
        ],
      ],
    );
  }
}

/// Ringkasan jumlah pasien per level dalam satu baris angka, seperti kepala papan pantau IGD.
class _Sensus extends StatelessWidget {
  const _Sensus({required this.jumlah, required this.belumDitriase});

  final Map<RiskLevel, int> jumlah;
  final int belumDitriase;

  @override
  Widget build(BuildContext context) {
    final sel = [
      for (final level in const [RiskLevel.kritis, RiskLevel.tinggi, RiskLevel.sedang, RiskLevel.rendah])
        (labelLevel(level), Warna.level(level), jumlah[level] ?? 0, '${labelLevel(level)}: ${jumlah[level] ?? 0}'),
      ('Belum', Warna.belum, belumDitriase, 'Belum ditriase: $belumDitriase'),
    ];
    return DecoratedBox(
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(bottom: BorderSide(color: Warna.garis)),
      ),
      child: Row(
        children: [
          for (final (i, (label, warna, n, bacaan)) in sel.indexed)
            Expanded(
              child: Semantics(
                container: true,
                label: '$bacaan pasien',
                excludeSemantics: true,
                child: Container(
                  padding: const EdgeInsets.only(top: 8, bottom: 8),
                  decoration: BoxDecoration(
                    border: Border(
                      top: BorderSide(color: warna, width: 4),
                      left: i == 0 ? BorderSide.none : const BorderSide(color: Warna.garisLembut),
                    ),
                  ),
                  child: Column(
                    children: [
                      Text(
                        '$n',
                        style: TextStyle(
                          fontSize: 22,
                          fontWeight: FontWeight.w700,
                          height: 1.15,
                          color: n == 0 ? Warna.nol : Warna.teks,
                        ),
                      ),
                      Text(
                        label,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(fontSize: 12, color: Warna.teksRedup),
                      ),
                    ],
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

class _BarisKeterangan extends StatelessWidget {
  const _BarisKeterangan({required this.jumlahPasien, required this.waktuMuat});

  final int jumlahPasien;
  final DateTime waktuMuat;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 10, 16, 10),
      child: Wrap(
        alignment: WrapAlignment.spaceBetween,
        spacing: 12,
        runSpacing: 4,
        children: [
          Text('$jumlahPasien pasien menunggu', style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700)),
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.sync, size: 16, color: Warna.teksSamar),
              const SizedBox(width: 4),
              Text('Diperbarui ${jamWib(waktuMuat)}', style: const TextStyle(fontSize: 14, color: Warna.teksSamar)),
            ],
          ),
        ],
      ),
    );
  }
}

/// Satu baris pasien di daftar tunggu: garis warna level di kiri, nama dan level, keluhan, lama tunggu, penanda,
/// dan tombol aksi untuk perawat.
class BarisPasienTunggu extends ConsumerWidget {
  const BarisPasienTunggu(this.item, {super.key});

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

    final batas = item.batasTungguMenit;
    final waktu = <Widget>[
      Text('Tunggu ${durasiMenit(item.lamaMenungguMenit)}'),
      if (triase != null && kritis)
        const Text(
          'segera',
          style: TextStyle(color: Warna.galat, fontWeight: FontWeight.w700),
        )
      else if (triase != null && lewat && batas != null)
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.schedule, size: 16, color: Warna.galat),
            const SizedBox(width: 3),
            Flexible(
              child: Text(
                'lewat batas $batas mnt',
                style: const TextStyle(color: Warna.galat, fontWeight: FontWeight.w700),
              ),
            ),
          ],
        )
      else if (triase != null && batas != null)
        Text('batas $batas mnt'),
    ];

    final tanda = <Widget>[
      if (lewat) const Tanda('Perlu triase ulang', warna: Warna.waspada, ikon: Icons.update),
      if (item.reviewDiajukan)
        const Tanda('Menunggu review dokter', warna: Warna.waspada, ikon: Icons.rate_review_outlined)
      else if (kritis && item.menungguValidasi)
        const Tanda('Menunggu dokter', warna: Warna.galat, ikon: Icons.priority_high),
      if (item.ringkasanEirSiap)
        const Tanda('Ringkasan Eir siap', warna: Warna.utama, ikon: Icons.description_outlined),
    ];

    final perawat = peran == Peran.perawat;
    final gayaAksi = OutlinedButton.styleFrom(
      minimumSize: const Size(48, 40),
      padding: const EdgeInsets.symmetric(horizontal: 12),
      textStyle: const TextStyle(fontFamily: hurufAplikasi, fontSize: 14, fontWeight: FontWeight.w700),
    );
    final aksi = <Widget>[
      if (perawat && (triase == null || lewat))
        OutlinedButton.icon(
          style: gayaAksi,
          onPressed: () => _bukaForm(context, ulang: triase != null),
          icon: const Icon(Icons.edit_note, size: 20),
          label: Text(triase == null ? 'Isi triase' : 'Triase ulang'),
        ),
      if (perawat && triase?.riskLevel == RiskLevel.rendah)
        OutlinedButton.icon(
          style: gayaAksi,
          onPressed: () => context.push(Rute.kodeQrEir(item.idKunjungan), extra: pasien),
          icon: const Icon(Icons.qr_code_2, size: 20),
          label: const Text('Kode QR Eir'),
        ),
    ];

    return Material(
      color: Colors.white,
      child: InkWell(
        onTap: () => _buka(context, peran),
        child: Container(
          decoration: BoxDecoration(
            border: Border(
              left: BorderSide(color: triase == null ? Warna.belum : Warna.level(triase.riskLevel), width: 5),
              bottom: const BorderSide(color: Warna.garis),
            ),
          ),
          padding: const EdgeInsets.fromLTRB(12, 12, 14, 12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Text(pasien.nama, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
                  ),
                  const SizedBox(width: 8),
                  if (triase != null) LencanaRisiko(triase.riskLevel) else const LencanaBelumTriase(),
                ],
              ),
              const SizedBox(height: 2),
              Text(identitas, style: const TextStyle(color: Warna.teksRedup, fontSize: 14)),
              if (triase != null) ...[
                const SizedBox(height: 5),
                Text(triase.keluhanUtama, style: const TextStyle(fontSize: 15)),
              ],
              const SizedBox(height: 6),
              DefaultTextStyle.merge(
                style: const TextStyle(color: Warna.teksRedup, fontSize: 14),
                child: Wrap(spacing: 12, runSpacing: 2, children: waktu),
              ),
              if (tanda.isNotEmpty || aksi.isNotEmpty) const SizedBox(height: 8),
              if (tanda.isEmpty && aksi.isNotEmpty)
                Align(
                  alignment: Alignment.centerRight,
                  child: Wrap(spacing: 8, runSpacing: 8, children: aksi),
                )
              else if (tanda.isNotEmpty)
                Wrap(
                  alignment: WrapAlignment.spaceBetween,
                  crossAxisAlignment: WrapCrossAlignment.center,
                  spacing: 12,
                  runSpacing: 8,
                  children: [...tanda, ...aksi],
                ),
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
