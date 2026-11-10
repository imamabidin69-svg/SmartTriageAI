import 'package:flutter/material.dart';

import '../api/galat_api.dart';
import '../api/generated/models/risk_level.dart';
import '../tema.dart';
import '../util/label.dart';

/// Penanda risk level. Hanya Kritis yang berlatar merah penuh supaya pasien paling gawat langsung menonjol;
/// level lain cukup kotak kecil berwarna dan teks, jadi level tetap terbaca tanpa mengandalkan warna.
class LencanaRisiko extends StatelessWidget {
  const LencanaRisiko(this.level, {super.key, this.besar = false});

  final RiskLevel level;
  final bool besar;

  @override
  Widget build(BuildContext context) {
    final label = Text(
      labelLevel(level),
      style: TextStyle(
        color: level == RiskLevel.kritis ? Colors.white : Warna.teks,
        fontWeight: FontWeight.w700,
        fontSize: besar ? 26 : 14,
        height: 1.2,
      ),
    );
    if (level == RiskLevel.kritis) {
      return Container(
        padding: EdgeInsets.symmetric(horizontal: besar ? 12 : 8, vertical: besar ? 4 : 3),
        decoration: BoxDecoration(color: Warna.kritis, borderRadius: BorderRadius.circular(4)),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            _Kotak(warna: Colors.white, sisi: besar ? 12 : 7),
            SizedBox(width: besar ? 10 : 6),
            label,
          ],
        ),
      );
    }
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        _Kotak(warna: Warna.level(level), sisi: besar ? 18 : 11),
        SizedBox(width: besar ? 10 : 6),
        label,
      ],
    );
  }
}

/// Penanda pasien yang belum ditriase: kotak kosong abu-abu, tanpa warna level.
class LencanaBelumTriase extends StatelessWidget {
  const LencanaBelumTriase({super.key});

  @override
  Widget build(BuildContext context) {
    return const Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        _Kotak(warna: Warna.belum, sisi: 11, kosong: true),
        SizedBox(width: 6),
        Text(
          'Belum ditriase',
          style: TextStyle(color: Warna.teksRedup, fontWeight: FontWeight.w700, fontSize: 14, height: 1.2),
        ),
      ],
    );
  }
}

class _Kotak extends StatelessWidget {
  const _Kotak({required this.warna, required this.sisi, this.kosong = false});

  final Color warna;
  final double sisi;
  final bool kosong;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: sisi,
      height: sisi,
      decoration: BoxDecoration(
        color: kosong ? null : warna,
        border: kosong ? Border.all(color: warna, width: 2) : null,
        borderRadius: BorderRadius.circular(2),
      ),
    );
  }
}

/// Keterangan singkat berikon tanpa latar, misalnya "Perlu triase ulang" atau "Ringkasan Eir siap".
class Tanda extends StatelessWidget {
  const Tanda(this.teks, {super.key, required this.warna, required this.ikon});

  final String teks;
  final Color warna;
  final IconData ikon;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(ikon, size: 18, color: warna),
        const SizedBox(width: 4),
        Flexible(
          child: Text(
            teks,
            style: TextStyle(color: warna, fontSize: 14, fontWeight: FontWeight.w700),
          ),
        ),
      ],
    );
  }
}

enum JenisPesan { galat, peringatan, info, sukses }

/// Kotak pesan dengan garis tepi kiri berwarna, dibacakan pembaca layar sebagai live region.
class KotakPesan extends StatelessWidget {
  const KotakPesan(this.pesan, {super.key, this.jenis = JenisPesan.galat, this.judul});

  final String pesan;
  final String? judul;
  final JenisPesan jenis;

  @override
  Widget build(BuildContext context) {
    final (warna, garis, ikon) = switch (jenis) {
      JenisPesan.galat => (Warna.galat, Warna.kritis, Icons.error_outline),
      JenisPesan.peringatan => (Warna.waspada, Warna.waspadaGaris, Icons.warning_amber_rounded),
      JenisPesan.info => (Warna.utama, Warna.utama, Icons.info_outline),
      JenisPesan.sukses => (Warna.kepala, Warna.kepala, Icons.check_circle_outline),
    };
    return Semantics(
      liveRegion: true,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.fromLTRB(12, 12, 14, 12),
        decoration: BoxDecoration(
          color: Colors.white,
          border: Border(
            left: BorderSide(color: garis, width: 4),
            top: const BorderSide(color: Warna.garis),
            right: const BorderSide(color: Warna.garis),
            bottom: const BorderSide(color: Warna.garis),
          ),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(ikon, color: warna, size: 20),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (judul != null)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 2),
                      child: Text(
                        judul!,
                        style: TextStyle(color: warna, fontWeight: FontWeight.w700),
                      ),
                    ),
                  Text(pesan, style: const TextStyle(color: Warna.teks, height: 1.4)),
                ],
              ),
            ),
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
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
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
          const SizedBox.square(dimension: 28, child: CircularProgressIndicator(strokeWidth: 3)),
          if (pesan != null) ...[
            const SizedBox(height: 14),
            Text(pesan!, style: const TextStyle(color: Warna.teksRedup)),
          ],
        ],
      ),
    );
  }
}

/// Blok putih selebar layar dengan garis atas dan bawah, pengganti kartu bersudut besar. Judul opsional,
/// dengan aksi di kanan (misalnya tombol Pindai layar alat).
class KartuBagian extends StatelessWidget {
  const KartuBagian({super.key, this.judul, this.aksi, required this.child});

  final String? judul;
  final Widget? aksi;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    // Material (bukan DecoratedBox) supaya efek sentuh ListTile di dalam blok tetap terlihat.
    return Material(
      color: Colors.white,
      shape: const Border.symmetric(horizontal: BorderSide(color: Warna.garis)),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 14, 16, 16),
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
                    if (judul != null)
                      Semantics(
                        header: true,
                        child: Text(judul!, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
                      ),
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

/// Bilah tombol yang selalu terlihat di bawah layar, misalnya tombol keputusan dokter atau Hitung rekomendasi.
class BilahBawah extends StatelessWidget {
  const BilahBawah({super.key, required this.tombol});

  final List<Widget> tombol;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(top: BorderSide(color: Warna.garis)),
      ),
      child: SafeArea(
        top: false,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 10, 16, 12),
          // IntrinsicHeight supaya dua tombol sama tinggi walau label salah satunya turun baris.
          child: IntrinsicHeight(
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                for (final (i, t) in tombol.indexed) ...[if (i > 0) const SizedBox(width: 10), Expanded(child: t)],
              ],
            ),
          ),
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
          ? const SizedBox.square(
              dimension: 22,
              child: CircularProgressIndicator(strokeWidth: 2.5, color: Warna.teksSamar),
            )
          : Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                if (ikon != null) ...[Icon(ikon, size: 20), const SizedBox(width: 8)],
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
