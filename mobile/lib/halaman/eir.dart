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

/// Kode QR Eir (FR-08, keputusan M7). Perawat menunjukkan kode ini kepada keluarga pasien ICU, yang lalu membuka
/// halaman Eir di peramban ponsel mereka dan menjawab pertanyaan tentang riwayat pasien. Tautan berlaku dua jam.
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
        padding: const EdgeInsets.only(bottom: 24),
        children: [
          if (pasien != null) IdentitasPasien(pasien),
          const SizedBox(height: 12),
          if (_memuat)
            const Padding(
              padding: EdgeInsets.all(48),
              child: TampilanMemuat(pesan: 'Membuat kode QR...'),
            )
          else if (galat != null)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  KotakPesan(galat.pesan),
                  const SizedBox(height: 12),
                  OutlinedButton.icon(
                    onPressed: _buat,
                    icon: const Icon(Icons.refresh),
                    label: const Text('Coba lagi'),
                  ),
                ],
              ),
            )
          else if (tautan != null) ...[
            KartuBagian(
              child: Column(
                children: [
                  Semantics(
                    label: 'Kode QR tautan Eir',
                    child: QrImageView(
                      data: tautan.url,
                      size: 248,
                      backgroundColor: Colors.white,
                      eyeStyle: const QrEyeStyle(eyeShape: QrEyeShape.square, color: Warna.kepala),
                      dataModuleStyle: const QrDataModuleStyle(
                        dataModuleShape: QrDataModuleShape.square,
                        color: Warna.kepala,
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    'Berlaku sampai ${jamWib(tautan.kedaluwarsa)} WIB',
                    style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16),
                  ),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const KotakPesan(
                    'Minta keluarga pasien memindai kode ini dengan kamera ponsel, lalu menjawab pertanyaan Eir tentang '
                    'riwayat penyakit, obat rutin, dan alergi pasien. Ringkasannya muncul di papan prioritas sebagai '
                    '"Ringkasan Eir siap", dan informasi penting seperti alergi obat muncul di peringatan.',
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
                  TextButton.icon(
                    onPressed: _buat,
                    icon: const Icon(Icons.refresh),
                    label: const Text('Buat kode baru'),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}

/// Ringkasan riwayat dari keluarga dan percakapan Eir terakhir untuk satu pasien ICU.
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
      StatusSesiEir.dihentikan => 'Percakapan dihentikan',
      StatusSesiEir.$unknown => '-',
    };
    return ListView(
      padding: const EdgeInsets.only(bottom: 24),
      children: [
        DecoratedBox(
          decoration: const BoxDecoration(
            color: Colors.white,
            border: Border(bottom: BorderSide(color: Warna.garis)),
          ),
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 13),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (widget.namaPasien != null)
                  Text(widget.namaPasien!, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700)),
                Text(
                  '$status · dijawab ${data.pengisi == PengisiEir.keluarga ? 'keluarga' : 'pasien'} · '
                  'mulai ${jamWib(data.waktuPersetujuan)}',
                  style: const TextStyle(color: Warna.teksRedup, fontSize: 14),
                ),
              ],
            ),
          ),
        ),
        if (tandaBahaya != null)
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
            child: KotakPesan(
              tandaBahaya.split('; ').map((label) => '• $label').join('\n'),
              judul: 'Informasi penting dari keluarga',
              jenis: JenisPesan.peringatan,
            ),
          ),
        if (ringkasan != null) ...[
          const SizedBox(height: 12),
          KartuBagian(
            judul: 'Ringkasan riwayat untuk perawat',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                for (final (label, isi) in [
                  ('Kronologi sebelum masuk ICU', ringkasan.kronologi),
                  ('Riwayat penyakit', ringkasan.riwayatPenyakit),
                  ('Obat rutin', ringkasan.obatRutin),
                  ('Alergi', ringkasan.alergi),
                  ('Informasi lain', ringkasan.informasiLain),
                ]) ...[
                  Text(label, style: const TextStyle(color: Warna.teksRedup, fontSize: 13)),
                  const SizedBox(height: 1),
                  Text(isi, style: const TextStyle(fontSize: 15)),
                  const SizedBox(height: 8),
                ],
                const Text(
                  'Ringkasan disusun dari jawaban keluarga, jadi periksa ulang sebelum dipakai.',
                  style: TextStyle(color: Warna.teksSamar, fontSize: 13),
                ),
              ],
            ),
          ),
        ],
        const SizedBox(height: 12),
        KartuBagian(
          judul: 'Transkrip',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              if (data.transkrip.isEmpty) const Text('Belum ada pesan.', style: TextStyle(color: Warna.teksRedup)),
              for (final pesan in data.transkrip)
                _GelembungTranskrip(pesan.teks, dariEir: pesan.peran == ItemTranskripPeran.eir),
            ],
          ),
        ),
      ],
    );
  }
}

/// Pesan di transkrip Eir: pertanyaan Eir di kiri berlabel nama, jawaban pasien di kanan berwarna biru tua.
class _GelembungTranskrip extends StatelessWidget {
  const _GelembungTranskrip(this.teks, {required this.dariEir});

  final String teks;
  final bool dariEir;

  @override
  Widget build(BuildContext context) {
    final lebarMaks = MediaQuery.sizeOf(context).width * 0.8;
    return Align(
      alignment: dariEir ? Alignment.centerLeft : Alignment.centerRight,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 5),
        child: Column(
          crossAxisAlignment: dariEir ? CrossAxisAlignment.start : CrossAxisAlignment.end,
          children: [
            if (dariEir)
              const Padding(
                padding: EdgeInsets.only(bottom: 3),
                child: Text(
                  'Eir',
                  style: TextStyle(color: Warna.teksSamar, fontSize: 12.5, fontWeight: FontWeight.w700),
                ),
              ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 10),
              constraints: BoxConstraints(maxWidth: lebarMaks),
              decoration: BoxDecoration(
                color: dariEir ? Warna.latar : Warna.kepala,
                borderRadius: BorderRadius.only(
                  topLeft: Radius.circular(dariEir ? 2 : 12),
                  topRight: Radius.circular(dariEir ? 12 : 2),
                  bottomLeft: const Radius.circular(12),
                  bottomRight: const Radius.circular(12),
                ),
              ),
              child: Text(teks, style: TextStyle(color: dariEir ? Warna.teks : Colors.white, height: 1.45)),
            ),
          ],
        ),
      ),
    );
  }
}
