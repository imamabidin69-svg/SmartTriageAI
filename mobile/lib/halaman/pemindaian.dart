import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/galat_api.dart';
import '../api/generated/models/hasil_pemindaian_response.dart';
import '../api/generated/models/jenis_alat.dart';
import '../komponen/umum.dart';
import '../state/penyedia.dart';
import '../tema.dart';
import '../util/format.dart';
import '../util/label.dart';

/// Angka yang dikonfirmasi perawat, dikembalikan ke Form Triase.
class HasilPindai {
  const HasilPindai({required this.idPemindaian, required this.alat, required this.nilai});

  final String idPemindaian;
  final JenisAlat alat;

  /// Hanya kolom yang terbaca. Kolom kosong diisi manual di form.
  final Map<String, num> nilai;
}

/// Kamera Pemindaian (SKPL Tabel 7.1 no. 5, FR-04): ambil foto layar alat lalu tampilkan angka terbaca untuk
/// dikonfirmasi. Foto tidak disimpan di galeri maupun di server.
class HalamanPemindaian extends ConsumerStatefulWidget {
  const HalamanPemindaian({super.key});

  @override
  ConsumerState<HalamanPemindaian> createState() => _HalamanPemindaianState();
}

class _HalamanPemindaianState extends ConsumerState<HalamanPemindaian> {
  JenisAlat _alat = JenisAlat.tensimeter;
  bool _sibuk = false;
  HasilPemindaianResponse? _hasil;
  GalatApi? _galat;

  Future<void> _ambilFoto() async {
    setState(() {
      _galat = null;
      _hasil = null;
    });
    final File? foto;
    try {
      foto = await ref.read(pengambilFotoProvider)();
    } catch (_) {
      if (mounted) {
        setState(
          () => _galat = const GalatApi(
            status: -1,
            tipe: 'kamera',
            judul: 'Kamera tidak bisa dibuka. Periksa izin kamera atau isi tanda vital manual.',
          ),
        );
      }
      return;
    }
    if (foto == null || !mounted) return;
    setState(() => _sibuk = true);
    try {
      final hasil = await ref.read(repositoriProvider).pindai(_alat, foto);
      if (mounted) setState(() => _hasil = hasil);
    } on GalatApi catch (galat) {
      if (mounted) setState(() => _galat = galat);
    } finally {
      // Foto sementara langsung dihapus dari cache aplikasi (FR-04).
      try {
        foto.deleteSync();
      } on FileSystemException {
        // Berkas sudah tidak ada.
      }
      if (mounted) setState(() => _sibuk = false);
    }
  }

  void _pakai(HasilPemindaianResponse hasil) {
    final terbaca = <String, num>{
      for (final MapEntry(:key, :value) in hasil.nilai.entries)
        if (value is num) key: value,
    };
    Navigator.of(context).pop(HasilPindai(idPemindaian: hasil.idPemindaian, alat: hasil.jenisAlat, nilai: terbaca));
  }

  @override
  Widget build(BuildContext context) {
    final hasil = _hasil;
    final galat = _galat;
    return Scaffold(
      appBar: AppBar(title: const Text('Pindai Layar Alat')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          KartuBagian(
            judul: 'Jenis alat',
            child: Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                for (final alat in JenisAlat.$valuesDefined)
                  ChoiceChip(
                    label: Text(labelAlat(alat)),
                    selected: _alat == alat,
                    onSelected: _sibuk ? null : (_) => setState(() => _alat = alat),
                  ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          const KotakPesan(
            'Foto layar alat dari depan, tidak silau, dan semua angka terlihat. Foto tidak disimpan di galeri '
            'maupun di server.',
            jenis: JenisPesan.info,
          ),
          const SizedBox(height: 16),
          TombolProses(
            label: hasil == null ? 'Ambil foto' : 'Foto ulang',
            ikon: Icons.photo_camera_outlined,
            sibuk: _sibuk,
            onPressed: _ambilFoto,
          ),
          if (_sibuk) ...[
            const SizedBox(height: 12),
            const Text('Membaca angka dari foto...', textAlign: TextAlign.center),
          ],
          if (galat != null) ...[const SizedBox(height: 16), KotakPesan(galat.field('berkas') ?? galat.pesan)],
          if (hasil != null) ...[const SizedBox(height: 16), _HasilBaca(hasil, onPakai: () => _pakai(hasil))],
        ],
      ),
    );
  }
}

class _HasilBaca extends StatelessWidget {
  const _HasilBaca(this.hasil, {required this.onPakai});

  final HasilPemindaianResponse hasil;
  final VoidCallback onPakai;

  @override
  Widget build(BuildContext context) {
    if (!hasil.pembacaTersedia) {
      return const KotakPesan(
        'Pembaca layar belum tersedia di server. Isi tanda vital secara manual.',
        jenis: JenisPesan.peringatan,
      );
    }
    final kolom = [
      for (final k in urutanTandaVital)
        if (hasil.nilai.containsKey(k)) k,
    ];
    final terbaca = kolom.where((k) => hasil.nilai[k] is num).length;
    return KartuBagian(
      judul: 'Angka terbaca',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          for (final k in kolom)
            _BarisNilai(label: labelTandaVital[k]!, nilai: hasil.nilai[k], keyakinan: hasil.keyakinan[k]),
          const SizedBox(height: 8),
          if (terbaca < kolom.length)
            const Padding(
              padding: EdgeInsets.only(bottom: 12),
              child: KotakPesan(
                'Kolom yang tidak terbaca dibiarkan kosong untuk diisi manual.',
                jenis: JenisPesan.peringatan,
              ),
            ),
          FilledButton(
            onPressed: terbaca == 0 ? null : onPakai,
            child: Text(terbaca == 0 ? 'Tidak ada angka terbaca' : 'Pakai angka ini'),
          ),
        ],
      ),
    );
  }
}

class _BarisNilai extends StatelessWidget {
  const _BarisNilai({required this.label, required this.nilai, required this.keyakinan});

  final String label;
  final Object? nilai;
  final Object? keyakinan;

  @override
  Widget build(BuildContext context) {
    final angkaNilai = nilai is num ? angka(nilai! as num) : null;
    final persenYakin = keyakinan is num ? '${((keyakinan! as num) * 100).round()}% yakin' : null;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Expanded(child: Text(label)),
          Text(
            angkaNilai ?? 'tidak terbaca',
            style: TextStyle(
              fontSize: angkaNilai == null ? 14 : 20,
              fontWeight: FontWeight.w700,
              color: angkaNilai == null ? Warna.teksRedup : Warna.teks,
            ),
          ),
          if (persenYakin != null) ...[
            const SizedBox(width: 8),
            Text(persenYakin, style: const TextStyle(color: Warna.teksRedup, fontSize: 12)),
          ],
        ],
      ),
    );
  }
}
