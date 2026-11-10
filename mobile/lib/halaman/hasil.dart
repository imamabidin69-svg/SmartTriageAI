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
import '../api/generated/models/tanda_vital_response.dart';
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
    final keputusan = detail == null ? const <Widget>[] : _tombolKeputusan(detail, ref.watch(peranProvider));
    return Scaffold(
      appBar: AppBar(title: const Text('Hasil Triase')),
      body: detail != null
          ? RefreshIndicator(onRefresh: _muat, child: _isi(detail))
          : galat != null
          ? TampilanGalat(galat, cobaLagi: _muat)
          : const TampilanMemuat(pesan: 'Memuat hasil triase...'),
      // Tombol keputusan selalu terlihat di bawah, jadi dokter tidak perlu menggulir sampai akhir halaman.
      bottomNavigationBar: keputusan.isEmpty ? null : BilahBawah(tombol: keputusan),
    );
  }

  /// Setujui, koreksi, atau ajukan review: hanya selama hasil belum diputuskan.
  List<Widget> _tombolKeputusan(TriaseDetail detail, Peran? peran) {
    final status = detail.statusValidasi;
    final belumDiputuskan = status == StatusValidasi.menunggu || status == StatusValidasi.menungguReviewDokter;
    Widget setujui(bool dokter) =>
        TombolProses(label: 'Setujui', ikon: Icons.check, sibuk: _sibuk, onPressed: () => _setujui(dokter));
    if (peran == Peran.perawat && status == StatusValidasi.menunggu) {
      return [
        OutlinedButton(
          onPressed: _sibuk ? null : _ajukanReview,
          child: const Text('Ajukan review dokter', textAlign: TextAlign.center),
        ),
        if (detail.riskLevel != RiskLevel.kritis) setujui(false),
      ];
    }
    if (peran == Peran.dokter && belumDiputuskan) {
      return [
        OutlinedButton(
          onPressed: _sibuk ? null : () => _koreksi(detail.riskLevel),
          child: const Text('Koreksi risk level', textAlign: TextAlign.center),
        ),
        setujui(true),
      ];
    }
    return const [];
  }

  Widget _isi(TriaseDetail detail) {
    final peran = ref.watch(peranProvider);
    final pasien = detail.pasien;
    final faktor = detail.penjelasanAi.faktor.take(3).toList();
    final kontribusiMaks = faktor.map((f) => f.kontribusi.abs().toDouble()).fold(0.0, (a, b) => a > b ? a : b);
    final aksi = _aksi(detail, peran);
    return ListView(
      padding: const EdgeInsets.only(bottom: 24),
      children: [
        _BlokIdentitas(pasien, keterangan: '${labelJenisTriase(detail.jenis)} · ${tanggalJamWib(detail.waktuTriase)}'),
        _PanelLevel(detail),
        const SizedBox(height: 10),
        KartuBagian(
          judul: 'Faktor yang paling berpengaruh',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: faktor.isEmpty
                ? [const Text('Tidak ada faktor penjelas.', style: TextStyle(color: Warna.teksRedup))]
                : [
                    for (final (i, f) in faktor.indexed)
                      _BarisFaktor(
                        f,
                        model: detail.sumberRekomendasi == SumberRekomendasi.model,
                        porsi: kontribusiMaks == 0 ? 0.0 : f.kontribusi.abs() / kontribusiMaks,
                        pertama: i == 0,
                      ),
                  ],
          ),
        ),
        if (detail.peringatan.isNotEmpty)
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 10, 16, 0),
            child: KotakPesan(
              detail.peringatan.map((p) => '• ${p.pesan}').join('\n'),
              judul: 'Nilai yang perlu diperhatikan',
              jenis: JenisPesan.peringatan,
            ),
          ),
        const SizedBox(height: 10),
        KartuBagian(
          judul: 'Tanda vital',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _KisiTandaVital(detail.tandaVital, skalaNyeri: detail.skalaNyeri),
              const SizedBox(height: 8),
              _BarisData('Sumber tanda vital', labelSumberTandaVital(detail.sumberTandaVital)),
            ],
          ),
        ),
        const SizedBox(height: 10),
        KartuBagian(
          judul: 'Data triase',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _BarisData('Keluhan utama', detail.keluhanUtama),
              _BarisData('Gejala', detail.gejala),
              if (detail.kategoriKeluhan != null) _BarisData('Kategori', detail.kategoriKeluhan!.json ?? '-'),
              _BarisData('Kesadaran', labelKesadaran(detail.tingkatKesadaran)),
              _BarisData('Diinput oleh', detail.dibuatOleh.nama),
              if (detail.divalidasiOleh != null) _BarisData('Divalidasi oleh', detail.divalidasiOleh!.nama),
              if (detail.catatanValidasiTerakhir != null) _BarisData('Catatan', detail.catatanValidasiTerakhir!),
            ],
          ),
        ),
        if (aksi.isNotEmpty) ...[
          const SizedBox(height: 16),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: aksi),
          ),
        ],
      ],
    );
  }

  /// Pesan status dan tindakan lain di bawah data triase. Tombol keputusan ada di [_tombolKeputusan].
  List<Widget> _aksi(TriaseDetail detail, Peran? peran) {
    final status = detail.statusValidasi;
    final statusKunjungan = _statusKunjungan;
    final masihMenunggu = statusKunjungan == StatusKunjungan.menunggu;
    final aksi = <Widget>[];
    void tambah(Widget tombol) => aksi.addAll([tombol, const SizedBox(height: 10)]);

    if (peran == Peran.perawat && status == StatusValidasi.menunggu && detail.riskLevel == RiskLevel.kritis) {
      tambah(
        const KotakPesan(
          'Hasil kritis harus divalidasi dokter. Segera sampaikan ke dokter, atau ajukan review.',
          jenis: JenisPesan.galat,
        ),
      );
    } else if (peran == Peran.perawat && status == StatusValidasi.menungguReviewDokter) {
      tambah(const KotakPesan('Menunggu review dokter.', jenis: JenisPesan.info));
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

/// Nama pasien dan keterangan singkat di bagian atas halaman, blok putih selebar layar.
class _BlokIdentitas extends StatelessWidget {
  const _BlokIdentitas(this.pasien, {this.keterangan});

  final PasienTriase pasien;
  final String? keterangan;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(bottom: BorderSide(color: Warna.garis)),
      ),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 13),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(pasien.nama, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700)),
            const SizedBox(height: 2),
            Text(
              [if (pasien.usia != null) '${pasien.usia} th', labelKelamin(pasien.jenisKelamin)].join(' · '),
              style: const TextStyle(color: Warna.teksRedup, fontSize: 15),
            ),
            if (keterangan != null) ...[
              const SizedBox(height: 2),
              Text(keterangan!, style: const TextStyle(color: Warna.teksSamar, fontSize: 14)),
            ],
          ],
        ),
      ),
    );
  }
}

/// Rekomendasi risk level dengan garis warna level di kiri, status validasi, dan sumber rekomendasi.
class _PanelLevel extends StatelessWidget {
  const _PanelLevel(this.detail);

  final TriaseDetail detail;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border(
          left: BorderSide(color: Warna.level(detail.riskLevel), width: 6),
          bottom: const BorderSide(color: Warna.garis),
        ),
      ),
      padding: const EdgeInsets.fromLTRB(12, 12, 16, 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Rekomendasi risk level',
            style: TextStyle(color: Warna.teksRedup, fontSize: 14, fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 6),
          LencanaRisiko(detail.riskLevel, besar: true),
          const SizedBox(height: 10),
          const Divider(color: Warna.garisLembut),
          const SizedBox(height: 10),
          _TandaStatus(detail.statusValidasi),
          const SizedBox(height: 6),
          Text(
            'Sumber: ${labelSumberRekomendasi(detail.sumberRekomendasi)}'
            '${detail.penjelasanAi.versiModel == null ? '' : ' (${detail.penjelasanAi.versiModel})'}',
            style: const TextStyle(color: Warna.teksRedup, fontSize: 14),
          ),
          if (detail.sumberRekomendasi == SumberRekomendasi.aturan)
            const Padding(
              padding: EdgeInsets.only(top: 10),
              child: KotakPesan(
                'Model AI sedang tidak tersedia, jadi rekomendasi dihitung dengan aturan cadangan dari ambang '
                'yang diatur admin.',
                jenis: JenisPesan.peringatan,
              ),
            ),
          const SizedBox(height: 8),
          const Text(
            'Hasil ini rekomendasi. Keputusan akhir tetap di tangan perawat dan dokter.',
            style: TextStyle(color: Warna.teksSamar, fontSize: 13),
          ),
        ],
      ),
    );
  }
}

/// Enam tanda vital dalam kisi tiga kolom, angka besar dan satuan kecil.
class _KisiTandaVital extends StatelessWidget {
  const _KisiTandaVital(this.tv, {required this.skalaNyeri});

  final TandaVitalResponse tv;
  final int? skalaNyeri;

  @override
  Widget build(BuildContext context) {
    final sel = [
      ('Tekanan darah', '${tv.tdSistolik}/${tv.tdDiastolik}', 'mmHg'),
      ('Nadi', '${tv.nadi}', 'x/mnt'),
      ('Napas', '${tv.lajuNapas}', 'x/mnt'),
      ('Suhu', angka(tv.suhu), '°C'),
      ('SpO₂', angka(tv.saturasi), '%'),
      ('Nyeri', skalaNyeri == null ? '-' : '$skalaNyeri', skalaNyeri == null ? '' : '/10'),
    ];
    Widget kotak((String, String, String) isi, {required bool kanan, required bool bawah}) {
      final (label, nilai, satuan) = isi;
      return Expanded(
        child: Container(
          padding: const EdgeInsets.fromLTRB(10, 9, 8, 10),
          decoration: BoxDecoration(
            border: Border(
              right: kanan ? const BorderSide(color: Warna.garisLembut) : BorderSide.none,
              bottom: bawah ? const BorderSide(color: Warna.garisLembut) : BorderSide.none,
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: const TextStyle(color: Warna.teksRedup, fontSize: 13)),
              const SizedBox(height: 2),
              Text.rich(
                TextSpan(
                  text: nilai,
                  style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700),
                  children: [
                    if (satuan.isNotEmpty)
                      TextSpan(
                        text: ' $satuan',
                        style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w400, color: Warna.teksSamar),
                      ),
                  ],
                ),
              ),
            ],
          ),
        ),
      );
    }

    return DecoratedBox(
      decoration: BoxDecoration(
        border: Border.all(color: Warna.garis),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Column(
        children: [
          for (final baris in [0, 1])
            IntrinsicHeight(
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  for (final kolom in [0, 1, 2]) kotak(sel[baris * 3 + kolom], kanan: kolom < 2, bawah: baris == 0),
                ],
              ),
            ),
        ],
      ),
    );
  }
}

class _TandaStatus extends StatelessWidget {
  const _TandaStatus(this.status);

  final StatusValidasi status;

  @override
  Widget build(BuildContext context) {
    final (warna, ikon) = switch (status) {
      StatusValidasi.disetujui => (Warna.kepala, Icons.verified_outlined),
      StatusValidasi.dikoreksi => (Warna.utama, Icons.edit_outlined),
      StatusValidasi.menungguReviewDokter => (Warna.waspada, Icons.rate_review_outlined),
      _ => (Warna.waspada, Icons.pending_actions),
    };
    return Tanda(labelStatusValidasi(status), warna: warna, ikon: ikon);
  }
}

/// Satu faktor penjelas: nama dan nilainya, arah pengaruh, dan batang sepanjang besar pengaruh dibanding faktor
/// terbesar. Warnanya netral karena warna merah sampai hijau khusus untuk level risiko.
class _BarisFaktor extends StatelessWidget {
  const _BarisFaktor(this.faktor, {required this.model, required this.porsi, required this.pertama});

  final FaktorResponse faktor;
  final bool model;
  final double porsi;
  final bool pertama;

  @override
  Widget build(BuildContext context) {
    final nilai = faktor.nilai;
    final (ikon, keterangan) = switch (faktor.arah) {
      FaktorResponseArah.naik => (Icons.arrow_upward, model ? 'mendukung level ini' : 'menambah poin risiko'),
      FaktorResponseArah.turun => (Icons.arrow_downward, 'menurunkan risiko'),
      _ => (Icons.remove, 'tidak ada aturan yang terpicu'),
    };
    final naik = faktor.arah == FaktorResponseArah.naik;
    return Container(
      padding: EdgeInsets.only(top: pertama ? 0 : 10, bottom: 10),
      decoration: BoxDecoration(
        border: pertama ? null : const Border(top: BorderSide(color: Warna.garisLembut)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text.rich(
            TextSpan(
              text: faktor.label,
              children: [
                if (nilai != null) ...[
                  const TextSpan(text: ': '),
                  TextSpan(
                    text: nilai is num ? angka(nilai) : '$nilai',
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
                ],
              ],
            ),
            style: const TextStyle(fontSize: 15),
          ),
          const SizedBox(height: 6),
          Row(
            children: [
              Expanded(
                flex: 3,
                child: Row(
                  children: [
                    Icon(ikon, size: 16, color: Warna.teksSamar),
                    const SizedBox(width: 3),
                    Flexible(
                      child: Text(keterangan, style: const TextStyle(color: Warna.teksSamar, fontSize: 13)),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                flex: 2,
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(3),
                  child: LinearProgressIndicator(
                    value: porsi.clamp(0.0, 1.0),
                    minHeight: 6,
                    backgroundColor: Warna.garisLembut,
                    color: naik ? Warna.kepala : const Color(0xFF8FA3BD),
                    semanticsLabel: 'Besar pengaruh',
                  ),
                ),
              ),
            ],
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
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(color: Warna.teksRedup, fontSize: 13)),
          const SizedBox(height: 1),
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
                const Text(
                  'Pilih level hasil koreksi.',
                  style: TextStyle(color: Warna.galat, fontSize: 13, fontWeight: FontWeight.w600),
                ),
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
  Widget build(BuildContext context) => _BlokIdentitas(pasien);
}
