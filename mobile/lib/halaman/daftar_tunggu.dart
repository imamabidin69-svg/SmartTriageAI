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
import '../konfigurasi.dart';
import '../rute.dart';
import '../state/antrean.dart';
import '../state/sesi.dart';
import '../tema.dart';
import '../util/format.dart';
import '../util/label.dart';

/// Papan Prioritas ICU (pengganti Daftar Tunggu SKPL Tabel 7.1 no. 2): pasien yang masih di ICU, sudah diurutkan
/// server menurut siapa yang harus ditangani lebih dulu. Setiap kartu memuat bed, level, skor NEWS2, peluang
/// memburuk, waktu sejak observasi terakhir dibanding intervalnya, dan penanda persetujuan dokter.
class HalamanDaftarTunggu extends ConsumerWidget {
  const HalamanDaftarTunggu({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final antrean = ref.watch(antreanProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Prioritas Pasien ICU'), actions: const [TombolPeringatan()]),
      body: switch (antrean) {
        AsyncData(:final value) => RefreshIndicator(
          onRefresh: () => ref.read(antreanProvider.notifier).muatUlang(),
          child: _IsiDaftar(value),
        ),
        AsyncError(:final error) => TampilanGalat(error, cobaLagi: () => ref.invalidate(antreanProvider)),
        _ => const TampilanMemuat(pesan: 'Memuat papan prioritas...'),
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
    var belumDinilai = 0;
    for (final item in items) {
      final level = item.triaseTerakhir?.riskLevel;
      if (level == null) {
        belumDinilai++;
      } else {
        jumlah[level] = (jumlah[level] ?? 0) + 1;
      }
    }
    return ListView(
      padding: const EdgeInsets.only(bottom: 24),
      physics: const AlwaysScrollableScrollPhysics(),
      children: [
        _Sensus(jumlah: jumlah, belumDinilai: belumDinilai),
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
              'Belum ada pasien yang dirawat di ICU.',
              textAlign: TextAlign.center,
              style: TextStyle(color: Warna.teksRedup),
            ),
          )
        else ...[
          const Divider(),
          for (final (i, item) in items.indexed) BarisPasienTunggu(item, urutan: i + 1),
        ],
      ],
    );
  }
}

/// Ringkasan jumlah pasien per level dalam satu baris angka, seperti kepala papan pantau ICU.
class _Sensus extends StatelessWidget {
  const _Sensus({required this.jumlah, required this.belumDinilai});

  final Map<RiskLevel, int> jumlah;
  final int belumDinilai;

  @override
  Widget build(BuildContext context) {
    final sel = [
      for (final level in const [RiskLevel.kritis, RiskLevel.tinggi, RiskLevel.sedang, RiskLevel.rendah])
        (labelLevel(level), Warna.level(level), jumlah[level] ?? 0, '${labelLevel(level)}: ${jumlah[level] ?? 0}'),
      ('Belum', Warna.belum, belumDinilai, 'Belum dinilai: $belumDinilai'),
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
          Text(
            '$jumlahPasien dari $jumlahBedIcu bed terisi',
            style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700),
          ),
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

/// Satu pasien di papan prioritas: garis warna level di kiri, nomor urut dan bed, nama dan level, dasar penilaian,
/// waktu sejak observasi terakhir, penanda, dan tombol aksi untuk perawat.
class BarisPasienTunggu extends ConsumerWidget {
  const BarisPasienTunggu(this.item, {super.key, this.urutan});

  final ItemDaftarTunggu item;

  /// Nomor urut prioritas di papan (1 = ditangani paling dulu).
  final int? urutan;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final peran = ref.watch(peranProvider);
    final triase = item.triaseTerakhir;
    final pasien = item.pasien;
    final terlambat = item.statusTanda == ItemDaftarTungguStatusTanda.observasiTerlambat;
    final tindakan = item.status == StatusKunjungan.ditangani;
    final identitas = [
      if (pasien.usia != null) '${pasien.usia} th',
      singkatanKelamin(pasien.jenisKelamin),
      if (item.diagnosisMasuk != null) item.diagnosisMasuk!,
    ].join(' · ');

    final batas = item.batasTungguMenit;
    final peluang = triase?.peluangPerburukan;
    final dasar = triase == null
        ? 'Belum dinilai · masuk ${jamWib(item.waktuDatang)}'
        : ['NEWS2 ${triase.skorNews2}', if (peluang != null) 'peluang memburuk ${persenPeluang(peluang)}'].join(' · ');
    final waktu = <Widget>[
      Text(
        triase == null
            ? 'Masuk ${durasiMenit(item.lamaMenungguMenit)} lalu'
            : 'Observasi ${durasiMenit(item.lamaMenungguMenit)} lalu',
      ),
      if (triase != null && terlambat && batas != null)
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.schedule, size: 16, color: Warna.galat),
            const SizedBox(width: 3),
            Flexible(
              child: Text(
                'lewat interval $batas mnt',
                style: const TextStyle(color: Warna.galat, fontWeight: FontWeight.w700),
              ),
            ),
          ],
        )
      else if (triase != null && batas != null)
        Text('interval $batas mnt'),
    ];

    final tanda = <Widget>[
      if (tindakan) const Tanda('Sedang tindakan', warna: Warna.utama, ikon: Icons.medical_services_outlined),
      if (terlambat) const Tanda('Observasi terlambat', warna: Warna.waspada, ikon: Icons.update),
      if (item.reviewDiajukan)
        const Tanda('Review diajukan', warna: Warna.waspada, ikon: Icons.rate_review_outlined)
      else if (item.menungguValidasi)
        const Tanda('Menunggu persetujuan dokter', warna: Warna.galat, ikon: Icons.priority_high),
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
      if (perawat)
        OutlinedButton.icon(
          style: gayaAksi,
          onPressed: () => _bukaForm(context, ulang: triase != null),
          icon: const Icon(Icons.edit_note, size: 20),
          label: Text(triase == null ? 'Nilai awal' : 'Observasi'),
        ),
      if (perawat)
        OutlinedButton.icon(
          style: gayaAksi,
          onPressed: () => context.push(Rute.kodeQrEir(item.idKunjungan), extra: pasien),
          icon: const Icon(Icons.qr_code_2, size: 20),
          label: const Text('QR Eir'),
        ),
    ];

    final bed = item.nomorBed;
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
                  if (urutan != null)
                    Semantics(
                      label: 'Prioritas ke-$urutan',
                      excludeSemantics: true,
                      child: Container(
                        width: 28,
                        margin: const EdgeInsets.only(right: 8, top: 1),
                        padding: const EdgeInsets.symmetric(vertical: 2),
                        decoration: BoxDecoration(
                          color: Warna.latar,
                          borderRadius: BorderRadius.circular(4),
                          border: Border.all(color: Warna.garis),
                        ),
                        child: Text(
                          '$urutan',
                          textAlign: TextAlign.center,
                          style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14),
                        ),
                      ),
                    ),
                  Expanded(
                    child: Wrap(
                      spacing: 8,
                      crossAxisAlignment: WrapCrossAlignment.center,
                      children: [
                        if (bed != null)
                          Text(
                            bed,
                            style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700, color: Warna.kepala),
                          ),
                        Text(pasien.nama, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
                      ],
                    ),
                  ),
                  const SizedBox(width: 8),
                  if (triase != null) LencanaRisiko(triase.riskLevel) else const LencanaBelumTriase(),
                ],
              ),
              const SizedBox(height: 2),
              Text(identitas, style: const TextStyle(color: Warna.teksRedup, fontSize: 14)),
              const SizedBox(height: 5),
              Text(dasar, style: const TextStyle(fontSize: 15)),
              const SizedBox(height: 4),
              DefaultTextStyle.merge(
                style: const TextStyle(color: Warna.teksRedup, fontSize: 14),
                child: Wrap(spacing: 12, runSpacing: 2, children: waktu),
              ),
              if (tanda.isNotEmpty) ...[const SizedBox(height: 8), Wrap(spacing: 12, runSpacing: 6, children: tanda)],
              if (aksi.isNotEmpty) ...[
                const SizedBox(height: 8),
                Align(
                  alignment: Alignment.centerRight,
                  child: Wrap(spacing: 8, runSpacing: 8, children: aksi),
                ),
              ],
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
        nomorBed: item.nomorBed,
        waktuDatang: item.waktuDatang,
        triaseUlang: ulang,
        ringkasanEirSiap: item.ringkasanEirSiap,
      ),
    );
  }

  void _buka(BuildContext context, Peran? peran) {
    final triase = item.triaseTerakhir;
    if (triase != null) {
      context.push(Rute.hasil(triase.idTriase));
    } else if (peran == Peran.perawat) {
      _bukaForm(context, ulang: false);
    } else {
      tampilkanPesan(context, 'Pasien ini belum dinilai perawat.');
    }
  }
}
