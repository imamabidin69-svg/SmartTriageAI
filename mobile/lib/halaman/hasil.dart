import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../api/galat_api.dart';
import '../api/generated/models/faktor_response.dart';
import '../api/generated/models/faktor_response_arah.dart';
import '../api/generated/models/pasien_triase.dart';
import '../api/generated/models/peran.dart';
import '../api/generated/models/risk_level.dart';
import '../api/generated/models/status_kunjungan.dart';
import '../api/generated/models/status_kunjungan_request_status.dart';
import '../api/generated/models/status_validasi.dart';
import '../api/generated/models/sumber_rekomendasi.dart';
import '../api/generated/models/triase_detail.dart';
import '../api/generated/models/validasi_request.dart';
import '../api/generated/models/validasi_request_aksi.dart';
import '../komponen/umum.dart';
import '../rute.dart';
import '../state/antrean.dart';
import '../state/penyedia.dart';
import '../state/sesi.dart';
import '../tema.dart';
import '../util/format.dart';
import '../util/label.dart';

/// Hasil dan Penjelasan (SKPL Tabel 7.1 no. 6, FR-05 dan FR-06): risk level, tiga faktor penjelas, sumber
/// rekomendasi, serta tombol Setujui, Koreksi, dan Ajukan Review sesuai peran.
class HalamanHasil extends ConsumerStatefulWidget {
  const HalamanHasil({super.key, required this.idTriase, this.info});

  final String idTriase;
  final InfoHasil? info;

  @override
  ConsumerState<HalamanHasil> createState() => _HalamanHasilState();
}

class _HalamanHasilState extends ConsumerState<HalamanHasil> {
  TriaseDetail? _detail;
  StatusKunjungan? _statusKunjungan;
  Object? _galatMuat;
  bool _sibuk = false;

  @override
  void initState() {
    super.initState();
    _detail = widget.info?.detail;
    _statusKunjungan = widget.info?.statusKunjungan;
    if (_detail == null) _muat();
  }

  Future<void> _muat() async {
    setState(() => _galatMuat = null);
    try {
      final detail = await ref.read(repositoriProvider).detailTriase(widget.idTriase);
      if (mounted) setState(() => _detail = detail);
    } on GalatApi catch (galat) {
      if (mounted) setState(() => _galatMuat = galat);
    }
  }

  Future<void> _validasi(ValidasiRequest data, String berhasil) async {
    setState(() => _sibuk = true);
    try {
      final detail = await ref.read(repositoriProvider).validasi(widget.idTriase, data);
      if (!mounted) return;
      setState(() => _detail = detail);
      unawaited(ref.read(antreanProvider.notifier).muatUlang());
      tampilkanPesan(context, berhasil);
    } on GalatApi catch (galat) {
      if (mounted) {
        tampilkanPesan(context, galat.field('alasan') ?? galat.field('risk_level') ?? galat.pesan, galat: true);
      }
    } finally {
      if (mounted) setState(() => _sibuk = false);
    }
  }

  Future<void> _ubahStatus(String idKunjungan, StatusKunjunganRequestStatus status) async {
    setState(() => _sibuk = true);
    try {
      final hasil = await ref.read(repositoriProvider).ubahStatusKunjungan(idKunjungan, status);
      if (!mounted) return;
      setState(() => _statusKunjungan = hasil.status);
      unawaited(ref.read(antreanProvider.notifier).muatUlang());
      tampilkanPesan(context, 'Status kunjungan: ${labelStatusKunjungan(hasil.status).toLowerCase()}.');
    } on GalatApi catch (galat) {
      if (mounted) tampilkanPesan(context, galat.pesan, galat: true);
    } finally {
      if (mounted) setState(() => _sibuk = false);
    }
  }

  Future<void> _ajukanReview() async {
    final alasan = await showDialog<String>(
      context: context,
      builder: (_) => const DialogAlasan(judul: 'Ajukan review dokter'),
    );
    if (alasan == null) return;
    await _validasi(
      ValidasiRequest(aksi: ValidasiRequestAksi.ajukanReview, riskLevel: null, alasan: alasan),
      'Review diajukan ke dokter.',
    );
  }

  Future<void> _setujui(bool dokter) async {
    final yakin = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Setujui hasil triase?'),
        content: Text(
          dokter
              ? 'Risk level ini akan tercatat disetujui atas nama Anda di log audit.'
              : 'Hasil non-kritis ini akan tercatat disetujui atas nama Anda di log audit.',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Batal')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Setujui')),
        ],
      ),
    );
    if (yakin != true) return;
    await _validasi(
      const ValidasiRequest(aksi: ValidasiRequestAksi.setujui, riskLevel: null, alasan: null),
      'Hasil triase disetujui.',
    );
  }

  Future<void> _koreksi(RiskLevel sekarang) async {
    final hasil = await showDialog<(RiskLevel, String)>(
      context: context,
      builder: (_) => DialogKoreksi(levelSekarang: sekarang),
    );
    if (hasil == null) return;
    await _validasi(
      ValidasiRequest(aksi: ValidasiRequestAksi.koreksi, riskLevel: hasil.$1, alasan: hasil.$2),
      'Risk level dikoreksi menjadi ${labelLevel(hasil.$1).toLowerCase()}.',
    );
  }

  @override
  Widget build(BuildContext context) {
    final detail = _detail;
    final galat = _galatMuat;
    return Scaffold(
      appBar: AppBar(title: const Text('Hasil Triase')),
      body: detail != null
          ? RefreshIndicator(onRefresh: _muat, child: _isi(detail))
          : galat != null
          ? TampilanGalat(galat, cobaLagi: _muat)
          : const TampilanMemuat(pesan: 'Memuat hasil triase...'),
    );
  }

  Widget _isi(TriaseDetail detail) {
    final peran = ref.watch(peranProvider);
    final pasien = detail.pasien;
    final faktor = detail.penjelasanAi.faktor.take(3).toList();
    final tv = detail.tandaVital;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text(
          '${labelJenisTriase(detail.jenis)} · ${tanggalJamWib(detail.waktuTriase)}',
          style: const TextStyle(color: Warna.teksRedup),
        ),
        Text(pasien.nama, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w700)),
        Text(
          [if (pasien.usia != null) '${pasien.usia} th', labelKelamin(pasien.jenisKelamin)].join(' · '),
          style: const TextStyle(color: Warna.teksRedup, fontSize: 16),
        ),
        const SizedBox(height: 16),
        KartuBagian(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Rekomendasi risk level', style: TextStyle(color: Warna.teksRedup)),
              const SizedBox(height: 8),
              Row(
                children: [
                  LencanaRisiko(detail.riskLevel, besar: true),
                  const SizedBox(width: 12),
                  Expanded(child: _TandaStatus(detail.statusValidasi)),
                ],
              ),
              const SizedBox(height: 12),
              Text(
                'Sumber: ${labelSumberRekomendasi(detail.sumberRekomendasi)}'
                '${detail.penjelasanAi.versiModel == null ? '' : ' (${detail.penjelasanAi.versiModel})'}',
              ),
              if (detail.sumberRekomendasi == SumberRekomendasi.aturan)
                const Padding(
                  padding: EdgeInsets.only(top: 8),
                  child: KotakPesan(
                    'Model AI sedang tidak tersedia, jadi rekomendasi dihitung dengan aturan cadangan dari ambang '
                    'yang diatur admin.',
                    jenis: JenisPesan.peringatan,
                  ),
                ),
              const SizedBox(height: 8),
              const Text(
                'Hasil ini rekomendasi. Keputusan akhir tetap di tangan perawat dan dokter.',
                style: TextStyle(color: Warna.teksRedup, fontSize: 13),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),
        KartuBagian(
          judul: 'Faktor yang paling berpengaruh',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: faktor.isEmpty
                ? [const Text('Tidak ada faktor penjelas.', style: TextStyle(color: Warna.teksRedup))]
                : [for (final f in faktor) _BarisFaktor(f, model: detail.sumberRekomendasi == SumberRekomendasi.model)],
          ),
        ),
        if (detail.peringatan.isNotEmpty) ...[
          const SizedBox(height: 12),
          KotakPesan(
            detail.peringatan.map((p) => '• ${p.pesan}').join('\n'),
            judul: 'Nilai yang perlu diperhatikan',
            jenis: JenisPesan.peringatan,
          ),
        ],
        const SizedBox(height: 12),
        KartuBagian(
          judul: 'Data triase',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _BarisData('Keluhan utama', detail.keluhanUtama),
              _BarisData('Gejala', detail.gejala),
              if (detail.kategoriKeluhan != null) _BarisData('Kategori', detail.kategoriKeluhan!.json ?? '-'),
              _BarisData('Kesadaran', labelKesadaran(detail.tingkatKesadaran)),
              if (detail.skalaNyeri != null) _BarisData('Skala nyeri', '${detail.skalaNyeri}/10'),
              _BarisData(
                'Tanda vital',
                'TD ${tv.tdSistolik}/${tv.tdDiastolik} · nadi ${tv.nadi} · napas ${tv.lajuNapas} · '
                    'suhu ${angka(tv.suhu)} °C · SpO₂ ${angka(tv.saturasi)}%',
              ),
              _BarisData('Sumber tanda vital', labelSumberTandaVital(detail.sumberTandaVital)),
              _BarisData('Diinput oleh', detail.dibuatOleh.nama),
              if (detail.divalidasiOleh != null) _BarisData('Divalidasi oleh', detail.divalidasiOleh!.nama),
              if (detail.catatanValidasiTerakhir != null) _BarisData('Catatan', detail.catatanValidasiTerakhir!),
            ],
          ),
        ),
        const SizedBox(height: 16),
        ..._aksi(detail, peran),
        const SizedBox(height: 24),
      ],
    );
  }

  List<Widget> _aksi(TriaseDetail detail, Peran? peran) {
    final status = detail.statusValidasi;
    final belumDiputuskan = status == StatusValidasi.menunggu || status == StatusValidasi.menungguReviewDokter;
    final statusKunjungan = _statusKunjungan;
    final masihMenunggu = statusKunjungan == StatusKunjungan.menunggu;
    final aksi = <Widget>[];
    void tambah(Widget tombol) => aksi.addAll([tombol, const SizedBox(height: 10)]);

    if (peran == Peran.perawat && status == StatusValidasi.menunggu) {
      if (detail.riskLevel != RiskLevel.kritis) {
        tambah(TombolProses(label: 'Setujui', ikon: Icons.check, sibuk: _sibuk, onPressed: () => _setujui(false)));
      } else {
        tambah(
          const KotakPesan(
            'Hasil kritis harus divalidasi dokter. Segera sampaikan ke dokter, atau ajukan review.',
            jenis: JenisPesan.galat,
          ),
        );
      }
      tambah(
        OutlinedButton.icon(
          onPressed: _sibuk ? null : _ajukanReview,
          icon: const Icon(Icons.forward_to_inbox_outlined),
          label: const Text('Ajukan review dokter'),
        ),
      );
    } else if (peran == Peran.perawat && status == StatusValidasi.menungguReviewDokter) {
      tambah(const KotakPesan('Menunggu review dokter.', jenis: JenisPesan.info));
    }
    if (peran == Peran.dokter && belumDiputuskan) {
      tambah(TombolProses(label: 'Setujui', ikon: Icons.check, sibuk: _sibuk, onPressed: () => _setujui(true)));
      tambah(
        OutlinedButton.icon(
          onPressed: _sibuk ? null : () => _koreksi(detail.riskLevel),
          icon: const Icon(Icons.edit_outlined),
          label: const Text('Koreksi risk level'),
        ),
      );
    }
    if (peran == Peran.dokter && statusKunjungan != null && statusKunjungan != StatusKunjungan.selesai) {
      final mulai = statusKunjungan == StatusKunjungan.menunggu;
      tambah(
        OutlinedButton.icon(
          onPressed: _sibuk
              ? null
              : () => _ubahStatus(
                  detail.idKunjungan,
                  mulai ? StatusKunjunganRequestStatus.ditangani : StatusKunjunganRequestStatus.selesai,
                ),
          icon: Icon(mulai ? Icons.medical_services_outlined : Icons.task_alt),
          label: Text(mulai ? 'Mulai periksa pasien' : 'Tandai kunjungan selesai'),
        ),
      );
    }
    if (peran == Peran.perawat && masihMenunggu) {
      tambah(
        OutlinedButton.icon(
          onPressed: () => context.push(
            Rute.formTriase(detail.idKunjungan),
            extra: InfoFormTriase(pasien: detail.pasien, triaseUlang: true),
          ),
          icon: const Icon(Icons.edit_note),
          label: const Text('Triase ulang'),
        ),
      );
      if (detail.riskLevel == RiskLevel.rendah) {
        tambah(
          OutlinedButton.icon(
            onPressed: () => context.push(Rute.kodeQrEir(detail.idKunjungan), extra: detail.pasien),
            icon: const Icon(Icons.qr_code_2),
            label: const Text('Kode QR Eir untuk pasien'),
          ),
        );
      }
    }
    tambah(
      TextButton.icon(
        onPressed: () => context.push(Rute.riwayatPasien(detail.pasien.idPasien), extra: detail.pasien),
        icon: const Icon(Icons.history),
        label: const Text('Riwayat triase pasien'),
      ),
    );
    return aksi;
  }
}

class _TandaStatus extends StatelessWidget {
  const _TandaStatus(this.status);

  final StatusValidasi status;

  @override
  Widget build(BuildContext context) {
    final (warna, latar) = switch (status) {
      StatusValidasi.disetujui => (Warna.sukses, Warna.suksesMuda),
      StatusValidasi.dikoreksi => (const Color(0xFF1D4ED8), Warna.infoMuda),
      StatusValidasi.menungguReviewDokter => (Warna.galat, Warna.galatMuda),
      _ => (Warna.peringatan, Warna.peringatanMuda),
    };
    return Align(
      alignment: Alignment.centerLeft,
      child: Tanda(labelStatusValidasi(status), warna: warna, latar: latar),
    );
  }
}

class _BarisFaktor extends StatelessWidget {
  const _BarisFaktor(this.faktor, {required this.model});

  final FaktorResponse faktor;
  final bool model;

  @override
  Widget build(BuildContext context) {
    final nilai = faktor.nilai;
    final teksNilai = nilai == null ? '' : ': ${nilai is num ? angka(nilai) : nilai}';
    final (ikon, warna, keterangan) = switch (faktor.arah) {
      FaktorResponseArah.naik => (
        Icons.arrow_upward,
        Warna.galat,
        model ? 'mendukung level ini' : 'menambah poin risiko',
      ),
      FaktorResponseArah.turun => (Icons.arrow_downward, Warna.sukses, 'menurunkan risiko'),
      _ => (Icons.remove, Warna.teksRedup, 'tidak ada aturan yang terpicu'),
    };
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(ikon, color: warna, size: 20),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('${faktor.label}$teksNilai', style: const TextStyle(fontWeight: FontWeight.w600)),
                Text(keterangan, style: const TextStyle(color: Warna.teksRedup, fontSize: 13)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _BarisData extends StatelessWidget {
  const _BarisData(this.label, this.isi);

  final String label;
  final String isi;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(color: Warna.teksRedup, fontSize: 13)),
          Text(isi, style: const TextStyle(fontSize: 15)),
        ],
      ),
    );
  }
}

/// Alasan wajib minimal 5 karakter untuk ajuan review dan koreksi (NFR-06).
String? periksaAlasan(String? teks) {
  final panjang = (teks ?? '').trim().length;
  if (panjang < 5) return 'Alasan minimal 5 karakter.';
  if (panjang > 500) return 'Alasan maksimal 500 karakter.';
  return null;
}

class DialogAlasan extends StatefulWidget {
  const DialogAlasan({super.key, required this.judul});

  final String judul;

  @override
  State<DialogAlasan> createState() => _DialogAlasanState();
}

class _DialogAlasanState extends State<DialogAlasan> {
  final _form = GlobalKey<FormState>();
  final _alasan = TextEditingController();

  @override
  void dispose() {
    _alasan.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(widget.judul),
      content: Form(
        key: _form,
        child: TextFormField(
          controller: _alasan,
          autofocus: true,
          minLines: 2,
          maxLines: 4,
          maxLength: 500,
          decoration: const InputDecoration(labelText: 'Alasan'),
          validator: periksaAlasan,
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: const Text('Batal')),
        FilledButton(
          onPressed: () {
            if (_form.currentState!.validate()) Navigator.pop(context, _alasan.text.trim());
          },
          child: const Text('Kirim'),
        ),
      ],
    );
  }
}

class DialogKoreksi extends StatefulWidget {
  const DialogKoreksi({super.key, required this.levelSekarang});

  final RiskLevel levelSekarang;

  @override
  State<DialogKoreksi> createState() => _DialogKoreksiState();
}

class _DialogKoreksiState extends State<DialogKoreksi> {
  final _form = GlobalKey<FormState>();
  final _alasan = TextEditingController();
  RiskLevel? _level;
  bool _dicoba = false;

  @override
  void dispose() {
    _alasan.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final pilihan = RiskLevel.$valuesDefined.where((l) => l != widget.levelSekarang).toList();
    return AlertDialog(
      title: const Text('Koreksi risk level'),
      content: SingleChildScrollView(
        child: Form(
          key: _form,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Level saat ini: ${labelLevel(widget.levelSekarang)}'),
              const SizedBox(height: 8),
              RadioGroup<RiskLevel>(
                groupValue: _level,
                onChanged: (level) => setState(() => _level = level),
                child: Column(
                  children: [
                    for (final level in pilihan)
                      RadioListTile<RiskLevel>(
                        value: level,
                        title: Text(labelLevel(level)),
                        contentPadding: EdgeInsets.zero,
                      ),
                  ],
                ),
              ),
              if (_dicoba && _level == null)
                const Text('Pilih level hasil koreksi.', style: TextStyle(color: Warna.galat, fontSize: 12)),
              const SizedBox(height: 8),
              TextFormField(
                controller: _alasan,
                minLines: 2,
                maxLines: 4,
                maxLength: 500,
                decoration: const InputDecoration(labelText: 'Alasan koreksi'),
                validator: periksaAlasan,
              ),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: const Text('Batal')),
        FilledButton(
          onPressed: () {
            setState(() => _dicoba = true);
            final level = _level;
            if (_form.currentState!.validate() && level != null) Navigator.pop(context, (level, _alasan.text.trim()));
          },
          child: const Text('Simpan koreksi'),
        ),
      ],
    );
  }
}

/// Header identitas pasien singkat, dipakai di halaman riwayat dan kode QR.
class IdentitasPasien extends StatelessWidget {
  const IdentitasPasien(this.pasien, {super.key});

  final PasienTriase pasien;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(pasien.nama, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w700)),
        Text(
          [if (pasien.usia != null) '${pasien.usia} th', labelKelamin(pasien.jenisKelamin)].join(' · '),
          style: const TextStyle(color: Warna.teksRedup),
        ),
      ],
    );
  }
}
