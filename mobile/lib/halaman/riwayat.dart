import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../api/galat_api.dart';
import '../api/generated/models/item_riwayat.dart';
import '../api/generated/models/pasien_ringkas.dart';
import '../api/generated/models/pasien_triase.dart';
import '../komponen/umum.dart';
import '../rute.dart';
import '../state/penyedia.dart';
import '../tema.dart';
import '../util/format.dart';
import '../util/label.dart';
import 'hasil.dart';

/// Tab Riwayat: mencari pasien lalu membuka Riwayat Triase Pasien.
class HalamanCariRiwayat extends ConsumerStatefulWidget {
  const HalamanCariRiwayat({super.key});

  @override
  ConsumerState<HalamanCariRiwayat> createState() => _HalamanCariRiwayatState();
}

class _HalamanCariRiwayatState extends ConsumerState<HalamanCariRiwayat> {
  final _cari = TextEditingController();
  List<PasienRingkas>? _hasil;
  bool _mencari = false;
  GalatApi? _galat;

  @override
  void dispose() {
    _cari.dispose();
    super.dispose();
  }

  Future<void> _jalankan() async {
    final kata = _cari.text.trim();
    if (kata.length < 2) {
      setState(
        () =>
            _galat = const GalatApi(status: 422, tipe: 'isian', judul: 'Ketik minimal 2 huruf nama, atau NIK lengkap.'),
      );
      return;
    }
    setState(() {
      _mencari = true;
      _galat = null;
    });
    try {
      final hasil = await ref.read(repositoriProvider).cariPasien(kata);
      if (mounted) setState(() => _hasil = hasil);
    } on GalatApi catch (galat) {
      if (mounted) setState(() => _galat = galat);
    } finally {
      if (mounted) setState(() => _mencari = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final hasil = _hasil;
    final galat = _galat;
    return Scaffold(
      appBar: AppBar(title: const Text('Riwayat Pasien')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          TextField(
            key: const ValueKey('cari-riwayat'),
            controller: _cari,
            textInputAction: TextInputAction.search,
            onSubmitted: (_) => _jalankan(),
            decoration: InputDecoration(
              labelText: 'Cari nama atau NIK pasien',
              errorText: galat == null ? null : galat.field('q') ?? galat.pesan,
              suffixIcon: _mencari
                  ? const Padding(padding: EdgeInsets.all(14), child: CircularProgressIndicator(strokeWidth: 2))
                  : IconButton(tooltip: 'Cari', icon: const Icon(Icons.search), onPressed: _jalankan),
            ),
          ),
          const SizedBox(height: 12),
          if (hasil != null && hasil.isEmpty)
            const Text('Pasien tidak ditemukan.', style: TextStyle(color: Warna.teksRedup))
          else if (hasil != null)
            Card(
              clipBehavior: Clip.antiAlias,
              child: Column(
                children: [
                  for (final (i, pasien) in hasil.indexed)
                    ListTile(
                      shape: i == hasil.length - 1 ? null : const Border(bottom: BorderSide(color: Warna.garisLembut)),
                      title: Text(pasien.nama),
                      subtitle: Text(
                        [
                          if (pasien.usia != null) '${pasien.usia} th',
                          labelKelamin(pasien.jenisKelamin),
                          if (pasien.nikTersamar != null) 'NIK ${pasien.nikTersamar}',
                        ].join(' · '),
                      ),
                      trailing: const Icon(Icons.chevron_right),
                      onTap: () => context.push(
                        Rute.riwayatPasien(pasien.idPasien),
                        extra: PasienTriase(
                          idPasien: pasien.idPasien,
                          nama: pasien.nama,
                          usia: pasien.usia,
                          jenisKelamin: pasien.jenisKelamin,
                        ),
                      ),
                    ),
                ],
              ),
            )
          else
            const Text(
              'Cari pasien untuk melihat triase awal dan triase ulangnya.',
              style: TextStyle(color: Warna.teksRedup),
            ),
        ],
      ),
    );
  }
}

/// Riwayat Triase Pasien (SKPL Tabel 7.1 no. 7, FR-09): rekam jejak triase awal dan triase ulang, terbaru dulu.
class HalamanRiwayatPasien extends ConsumerStatefulWidget {
  const HalamanRiwayatPasien({super.key, required this.idPasien, this.pasien});

  final String idPasien;
  final PasienTriase? pasien;

  @override
  ConsumerState<HalamanRiwayatPasien> createState() => _HalamanRiwayatPasienState();
}

class _HalamanRiwayatPasienState extends ConsumerState<HalamanRiwayatPasien> {
  final _items = <ItemRiwayat>[];
  PasienTriase? _pasien;
  String? _kursor;
  bool _memuat = true;
  bool _selesaiPertama = false;
  GalatApi? _galat;

  @override
  void initState() {
    super.initState();
    _pasien = widget.pasien;
    _muat();
  }

  Future<void> _muat({bool lanjutan = false}) async {
    setState(() {
      _memuat = true;
      _galat = null;
    });
    try {
      final hasil = await ref.read(repositoriProvider).riwayat(widget.idPasien, kursor: lanjutan ? _kursor : null);
      if (!mounted) return;
      setState(() {
        if (!lanjutan) _items.clear();
        _items.addAll(hasil.items);
        _kursor = hasil.kursorBerikutnya;
        _pasien = hasil.pasien;
        _selesaiPertama = true;
      });
    } on GalatApi catch (galat) {
      if (mounted) setState(() => _galat = galat);
    } finally {
      if (mounted) setState(() => _memuat = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final pasien = _pasien;
    final galat = _galat;
    return Scaffold(
      appBar: AppBar(title: const Text('Riwayat Triase')),
      body: !_selesaiPertama && galat != null
          ? TampilanGalat(galat, cobaLagi: _muat)
          : !_selesaiPertama
          ? const TampilanMemuat(pesan: 'Memuat riwayat...')
          : RefreshIndicator(
              onRefresh: _muat,
              child: ListView(
                padding: const EdgeInsets.only(bottom: 24),
                children: [
                  if (pasien != null) IdentitasPasien(pasien),
                  const SizedBox(height: 12),
                  if (_items.isEmpty)
                    const Padding(
                      padding: EdgeInsets.symmetric(horizontal: 16),
                      child: Text('Pasien ini belum pernah ditriase.', style: TextStyle(color: Warna.teksRedup)),
                    )
                  else ...[
                    const Divider(),
                    for (final item in _items) _KartuRiwayat(item),
                  ],
                  if (galat != null)
                    Padding(padding: const EdgeInsets.fromLTRB(16, 12, 16, 0), child: KotakPesan(galat.pesan)),
                  if (_kursor != null)
                    Padding(
                      padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
                      child: OutlinedButton(
                        onPressed: _memuat ? null : () => _muat(lanjutan: true),
                        child: Text(_memuat ? 'Memuat...' : 'Muat lebih banyak'),
                      ),
                    ),
                ],
              ),
            ),
    );
  }
}

/// Satu triase di riwayat pasien: baris putih dengan garis warna level di kiri, seperti di daftar tunggu.
class _KartuRiwayat extends StatelessWidget {
  const _KartuRiwayat(this.item);

  final ItemRiwayat item;

  @override
  Widget build(BuildContext context) {
    final tv = item.tandaVital;
    return Material(
      color: Colors.white,
      child: InkWell(
        onTap: () => context.push(Rute.hasil(item.idTriase), extra: InfoHasil(statusKunjungan: item.kunjungan.status)),
        child: Container(
          decoration: BoxDecoration(
            border: Border(
              left: BorderSide(color: Warna.level(item.riskLevel), width: 5),
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
                    child: Text(
                      '${labelJenisTriase(item.jenis)} · ${tanggalJamWib(item.waktuTriase)}',
                      style: const TextStyle(fontWeight: FontWeight.w700, color: Warna.teksRedup, fontSize: 14),
                    ),
                  ),
                  const SizedBox(width: 8),
                  LencanaRisiko(item.riskLevel),
                ],
              ),
              const SizedBox(height: 4),
              Text(item.keluhanUtama, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
              const SizedBox(height: 4),
              Text(
                'TD ${tv.tdSistolik}/${tv.tdDiastolik} · nadi ${tv.nadi} · SpO₂ ${angka(tv.saturasi)}% · '
                'suhu ${angka(tv.suhu)} °C',
                style: const TextStyle(color: Warna.teksRedup, fontSize: 14),
              ),
              const SizedBox(height: 6),
              Text(
                [
                  labelStatusValidasi(item.statusValidasi),
                  'oleh ${item.dibuatOleh.nama}',
                  labelStatusKunjungan(item.kunjungan.status),
                ].join(' · '),
                style: const TextStyle(color: Warna.teksSamar, fontSize: 13),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
