import 'package:flutter/material.dart';

import '../api/galat_api.dart';
import '../api/generated/models/risk_level.dart';
import '../tema.dart';
import '../util/label.dart';

/// Badge risk level berisi penuh seperti di mockup Gambar 7.1.
class LencanaRisiko extends StatelessWidget {
  const LencanaRisiko(this.level, {super.key, this.besar = false});

  final RiskLevel level;
  final bool besar;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: besar ? 16 : 10, vertical: besar ? 8 : 4),
      decoration: BoxDecoration(color: Warna.level(level), borderRadius: BorderRadius.circular(8)),
      child: Text(
        labelLevel(level),
        style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: besar ? 22 : 14),
      ),
    );
  }
}

/// Label kecil berwarna, misalnya "Perlu triase ulang" atau "Ringkasan Eir siap".
class Tanda extends StatelessWidget {
  const Tanda(this.teks, {super.key, required this.warna, required this.latar});

  final String teks;
  final Color warna;
  final Color latar;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(color: latar, borderRadius: BorderRadius.circular(8)),
      child: Text(
        teks,
        style: TextStyle(color: warna, fontSize: 13, fontWeight: FontWeight.w500),
      ),
    );
  }
}

enum JenisPesan { galat, peringatan, info, sukses }

/// Kotak pesan di dalam halaman, dibacakan pembaca layar sebagai live region.
class KotakPesan extends StatelessWidget {
  const KotakPesan(this.pesan, {super.key, this.jenis = JenisPesan.galat, this.judul});

  final String pesan;
  final String? judul;
  final JenisPesan jenis;

  @override
  Widget build(BuildContext context) {
    final (warna, latar) = switch (jenis) {
      JenisPesan.galat => (Warna.galat, Warna.galatMuda),
      JenisPesan.peringatan => (Warna.peringatan, Warna.peringatanMuda),
      JenisPesan.info => (Warna.utama, Warna.infoMuda),
      JenisPesan.sukses => (Warna.sukses, Warna.suksesMuda),
    };
    return Semantics(
      liveRegion: true,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: latar,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: warna.withValues(alpha: 0.25)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (judul != null)
              Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Text(
                  judul!,
                  style: TextStyle(color: warna, fontWeight: FontWeight.w700),
                ),
              ),
            Text(pesan, style: TextStyle(color: warna)),
          ],
        ),
      ),
    );
  }
}

/// Tampilan saat data gagal dimuat, dengan tombol untuk mencoba lagi.
class TampilanGalat extends StatelessWidget {
  const TampilanGalat(this.galat, {super.key, required this.cobaLagi});

  final Object galat;
  final VoidCallback cobaLagi;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            KotakPesan(GalatApi.dari(galat).pesan),
            const SizedBox(height: 16),
            OutlinedButton.icon(onPressed: cobaLagi, icon: const Icon(Icons.refresh), label: const Text('Coba lagi')),
          ],
        ),
      ),
    );
  }
}

class TampilanMemuat extends StatelessWidget {
  const TampilanMemuat({super.key, this.pesan});

  final String? pesan;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const CircularProgressIndicator(),
          if (pesan != null) ...[
            const SizedBox(height: 12),
            Text(pesan!, style: const TextStyle(color: Warna.teksRedup)),
          ],
        ],
      ),
    );
  }
}

/// Kartu berjudul untuk mengelompokkan isian, seperti kartu "Tanda vital" di mockup.
class KartuBagian extends StatelessWidget {
  const KartuBagian({super.key, this.judul, this.aksi, required this.child});

  final String? judul;
  final Widget? aksi;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (judul != null || aksi != null)
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                // Wrap supaya tombol aksi turun ke baris berikutnya di layar sempit atau huruf besar.
                child: Wrap(
                  alignment: WrapAlignment.spaceBetween,
                  crossAxisAlignment: WrapCrossAlignment.center,
                  spacing: 12,
                  runSpacing: 8,
                  children: [
                    if (judul != null) Text(judul!, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
                    ?aksi,
                  ],
                ),
              ),
            child,
          ],
        ),
      ),
    );
  }
}

/// Tombol utama yang menampilkan indikator saat proses berjalan.
class TombolProses extends StatelessWidget {
  const TombolProses({super.key, required this.label, required this.onPressed, this.sibuk = false, this.ikon});

  final String label;
  final VoidCallback? onPressed;
  final bool sibuk;
  final IconData? ikon;

  @override
  Widget build(BuildContext context) {
    return FilledButton(
      onPressed: sibuk ? null : onPressed,
      child: sibuk
          ? const SizedBox.square(dimension: 22, child: CircularProgressIndicator(strokeWidth: 2.5))
          : Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                if (ikon != null) ...[Icon(ikon), const SizedBox(width: 8)],
                // Flexible supaya label turun baris bila ukuran huruf perangkat diperbesar.
                Flexible(child: Text(label, textAlign: TextAlign.center)),
              ],
            ),
    );
  }
}

/// Snackbar singkat untuk keberhasilan atau error yang tidak terkait satu kolom.
void tampilkanPesan(BuildContext context, String pesan, {bool galat = false}) {
  ScaffoldMessenger.of(context)
    ..hideCurrentSnackBar()
    ..showSnackBar(SnackBar(content: Text(pesan), backgroundColor: galat ? Warna.galat : null));
}
