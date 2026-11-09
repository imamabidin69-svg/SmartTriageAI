import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:qr_flutter/qr_flutter.dart';

import '../api/galat_api.dart';
import '../api/generated/models/item_transkrip_peran.dart';
import '../api/generated/models/pasien_triase.dart';
import '../api/generated/models/pengisi_eir.dart';
import '../api/generated/models/ringkasan_eir_response.dart';
import '../api/generated/models/status_sesi_eir.dart';
import '../api/generated/models/tautan_eir_response.dart';
import '../komponen/umum.dart';
import '../state/penyedia.dart';
import '../tema.dart';
import '../util/format.dart';
import 'hasil.dart';

/// Kode QR Eir (FR-08, keputusan M7). Perawat menunjukkan kode ini kepada pasien zona hijau atau keluarganya,
/// yang lalu membuka halaman Eir di peramban ponsel mereka. Tautan berlaku dua jam.
class HalamanKodeQrEir extends ConsumerStatefulWidget {
  const HalamanKodeQrEir({super.key, required this.idKunjungan, this.pasien});

  final String idKunjungan;
  final PasienTriase? pasien;

  @override
  ConsumerState<HalamanKodeQrEir> createState() => _HalamanKodeQrEirState();
}

class _HalamanKodeQrEirState extends ConsumerState<HalamanKodeQrEir> {
  TautanEirResponse? _tautan;
  GalatApi? _galat;
  bool _memuat = true;

  @override
  void initState() {
    super.initState();
    _buat();
  }

  Future<void> _buat() async {
    setState(() {
      _memuat = true;
      _galat = null;
    });
    try {
      final tautan = await ref.read(repositoriProvider).tautanEir(widget.idKunjungan);
      if (mounted) setState(() => _tautan = tautan);
    } on GalatApi catch (galat) {
      if (mounted) setState(() => _galat = galat);
    } finally {
      if (mounted) setState(() => _memuat = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final tautan = _tautan;
    final galat = _galat;
    final pasien = widget.pasien;
    return Scaffold(
      appBar: AppBar(title: const Text('Kode QR Eir')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (pasien != null) ...[IdentitasPasien(pasien), const SizedBox(height: 16)],
          if (_memuat)
            const Padding(
              padding: EdgeInsets.all(48),
              child: TampilanMemuat(pesan: 'Membuat kode QR...'),
            )
          else if (galat != null) ...[
            KotakPesan(galat.pesan),
            const SizedBox(height: 12),
            OutlinedButton.icon(onPressed: _buat, icon: const Icon(Icons.refresh), label: const Text('Coba lagi')),
          ] else if (tautan != null) ...[
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  children: [
                    Semantics(
                      label: 'Kode QR tautan Eir',
                      child: QrImageView(data: tautan.url, size: 260, backgroundColor: Colors.white),
                    ),
                    const SizedBox(height: 12),
                    Text(
                      'Berlaku sampai ${jamWib(tautan.kedaluwarsa)} WIB',
                      style: const TextStyle(fontWeight: FontWeight.w600),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),
            const KotakPesan(
              'Minta pasien atau keluarga memindai kode ini dengan kamera ponsel, lalu menjawab pertanyaan Eir '
              'sambil menunggu. Ringkasannya akan muncul di daftar tunggu sebagai "Ringkasan Eir siap".',
              jenis: JenisPesan.info,
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: () {
                Clipboard.setData(ClipboardData(text: tautan.url));
                tampilkanPesan(context, 'Tautan Eir disalin.');
              },
              icon: const Icon(Icons.copy),
              label: const Text('Salin tautan'),
            ),
            const SizedBox(height: 8),
            TextButton.icon(onPressed: _buat, icon: const Icon(Icons.refresh), label: const Text('Buat kode baru')),
          ],
        ],
      ),
    );
  }
}

/// Ringkasan dan percakapan Eir terakhir untuk satu kunjungan, dibuka dari peringatan tanda bahaya Eir.
class HalamanRingkasanEir extends ConsumerStatefulWidget {
  const HalamanRingkasanEir({super.key, required this.idKunjungan, this.namaPasien});

  final String idKunjungan;
  final String? namaPasien;

  @override
  ConsumerState<HalamanRingkasanEir> createState() => _HalamanRingkasanEirState();
}

class _HalamanRingkasanEirState extends ConsumerState<HalamanRingkasanEir> {
  RingkasanEirResponse? _data;
  GalatApi? _galat;

  @override
  void initState() {
    super.initState();
    _muat();
  }

  Future<void> _muat() async {
    setState(() => _galat = null);
    try {
      final data = await ref.read(repositoriProvider).ringkasanEir(widget.idKunjungan);
      if (mounted) setState(() => _data = data);
    } on GalatApi catch (galat) {
      if (mounted) setState(() => _galat = galat);
    }
  }

  @override
  Widget build(BuildContext context) {
    final data = _data;
    final galat = _galat;
    return Scaffold(
      appBar: AppBar(title: const Text('Percakapan Eir')),
      body: data != null
          ? _isi(data)
          : galat != null
          ? TampilanGalat(galat, cobaLagi: _muat)
          : const TampilanMemuat(pesan: 'Memuat percakapan Eir...'),
    );
  }

  Widget _isi(RingkasanEirResponse data) {
    final ringkasan = data.ringkasan;
    final tandaBahaya = data.tandaBahaya;
    final status = switch (data.status) {
      StatusSesiEir.berjalan => 'Percakapan masih berjalan',
      StatusSesiEir.selesai => 'Percakapan selesai',
      StatusSesiEir.dihentikan => 'Percakapan dihentikan karena tanda bahaya',
      StatusSesiEir.$unknown => '-',
    };
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (widget.namaPasien != null)
          Text(widget.namaPasien!, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w700)),
        Text(
          '$status · dijawab ${data.pengisi == PengisiEir.keluarga ? 'keluarga' : 'pasien'} · '
          'mulai ${jamWib(data.waktuPersetujuan)}',
          style: const TextStyle(color: Warna.teksRedup),
        ),
        const SizedBox(height: 16),
        if (tandaBahaya != null) ...[
          KotakPesan(tandaBahaya, judul: 'Tanda bahaya', jenis: JenisPesan.galat),
          const SizedBox(height: 12),
        ],
        if (ringkasan != null) ...[
          KartuBagian(
            judul: 'Ringkasan untuk perawat',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Keluhan utama: ${ringkasan.keluhanUtama}'),
                const SizedBox(height: 4),
                Text('Gejala: ${ringkasan.gejala}'),
                const SizedBox(height: 4),
                Text('Sejak: ${ringkasan.onset}'),
                const SizedBox(height: 4),
                Text('Kategori: ${ringkasan.kategoriKeluhan.json ?? '-'}'),
              ],
            ),
          ),
          const SizedBox(height: 12),
        ],
        const Text('Transkrip', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
        const SizedBox(height: 8),
        if (data.transkrip.isEmpty) const Text('Belum ada pesan.', style: TextStyle(color: Warna.teksRedup)),
        for (final pesan in data.transkrip)
          Align(
            alignment: pesan.peran == ItemTranskripPeran.eir ? Alignment.centerLeft : Alignment.centerRight,
            child: Container(
              margin: const EdgeInsets.symmetric(vertical: 4),
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              constraints: BoxConstraints(maxWidth: MediaQuery.sizeOf(context).width * 0.8),
              decoration: BoxDecoration(
                color: pesan.peran == ItemTranskripPeran.eir ? const Color(0xFFF1F5F9) : Warna.utama,
                borderRadius: BorderRadius.circular(16),
              ),
              child: Text(
                pesan.teks,
                style: TextStyle(color: pesan.peran == ItemTranskripPeran.eir ? Warna.teks : Colors.white),
              ),
            ),
          ),
      ],
    );
  }
}
