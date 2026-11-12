import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../api/galat_api.dart';
import '../api/generated/models/faktor_response.dart';
import '../api/generated/models/faktor_response_arah.dart';
import '../api/generated/models/jenis_triase.dart';
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

/// Hasil Penilaian (SKPL Tabel 7.1 no. 6, FR-05 dan FR-06, disesuaikan untuk ICU): level prioritas, skor NEWS2
/// dan komponennya, peluang memburuk dari model beserta tiga faktor SHAP, serta persetujuan dokter. Hanya dokter
/// yang menyetujui atau mengoreksi; perawat boleh mengajukan review.
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
    _statusKunjungan = _detail?.statusKunjungan;
    if (_detail == null) _muat();
  }

  Future<void> _muat() async {
    setState(() => _galatMuat = null);
    try {
      final detail = await ref.read(repositoriProvider).detailTriase(widget.idTriase);
      if (mounted) {
        setState(() {
          _detail = detail;
          _statusKunjungan = detail.statusKunjungan;
        });
      }
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
      tampilkanPesan(context, 'Status pasien: ${labelStatusKunjungan(hasil.status).toLowerCase()}.');
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

  Future<void> _keluarIcu(String idKunjungan) async {
    final yakin = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Tandai pasien keluar ICU?'),
        content: const Text(
          'Pasien hilang dari papan prioritas dan observasi baru tidak bisa ditambahkan. Bed bisa dipakai pasien lain.',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Batal')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Keluar ICU')),
        ],
      ),
    );
    if (yakin == true) await _ubahStatus(idKunjungan, StatusKunjunganRequestStatus.selesai);
  }

  Future<void> _setujui() async {
    final yakin = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Setujui prioritas pasien?'),
        content: const Text('Level ini akan tercatat disetujui atas nama Anda di log audit.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Batal')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Setujui')),
        ],
      ),
    );
    if (yakin != true) return;
    await _validasi(
      const ValidasiRequest(aksi: ValidasiRequestAksi.setujui, riskLevel: null, alasan: null),
      'Prioritas pasien disetujui.',
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
      'Level dikoreksi menjadi ${labelLevel(hasil.$1).toLowerCase()}.',
    );
  }

  @override
  Widget build(BuildContext context) {
    final detail = _detail;
    final galat = _galatMuat;
    final keputusan = detail == null ? const <Widget>[] : _tombolKeputusan(detail, ref.watch(peranProvider));
    return Scaffold(
      appBar: AppBar(title: const Text('Hasil Penilaian')),
      body: detail != null
          ? RefreshIndicator(onRefresh: _muat, child: _isi(detail))
          : galat != null
          ? TampilanGalat(galat, cobaLagi: _muat)
          : const TampilanMemuat(pesan: 'Memuat hasil penilaian...'),
      // Tombol keputusan selalu terlihat di bawah, jadi dokter tidak perlu menggulir sampai akhir halaman.
      bottomNavigationBar: keputusan.isEmpty ? null : BilahBawah(tombol: keputusan),
    );
  }

  /// Persetujuan dokter atau ajuan review perawat: hanya selama penilaian awal atau kenaikan level belum diputuskan.
  List<Widget> _tombolKeputusan(TriaseDetail detail, Peran? peran) {
    final status = detail.statusValidasi;
    final belumDiputuskan = status == StatusValidasi.menunggu || status == StatusValidasi.menungguReviewDokter;
    if (peran == Peran.perawat && status == StatusValidasi.menunggu) {
      return [
        OutlinedButton(
          onPressed: _sibuk ? null : _ajukanReview,
          child: const Text('Ajukan review dokter', textAlign: TextAlign.center),
        ),
      ];
    }
    if (peran == Peran.dokter && belumDiputuskan) {
      return [
        OutlinedButton(
          onPressed: _sibuk ? null : () => _koreksi(detail.riskLevel),
          child: const Text('Koreksi level', textAlign: TextAlign.center),
        ),
        TombolProses(label: 'Setujui', ikon: Icons.check, sibuk: _sibuk, onPressed: _setujui),
      ];
    }
    return const [];
  }

  Widget _isi(TriaseDetail detail) {
    final peran = ref.watch(peranProvider);
    final pasien = detail.pasien;
    final penjelasan = detail.penjelasanAi;
    final faktor = penjelasan.faktor.take(3).toList();
    final kontribusiMaks = faktor.map((f) => f.kontribusi.abs().toDouble()).fold(0.0, (a, b) => a > b ? a : b);
    final aksi = _aksi(detail, peran);
    final keterangan = [
      if (detail.nomorBed != null) 'Bed ${detail.nomorBed}',
      labelJenisTriase(detail.jenis),
      tanggalJamWib(detail.waktuTriase),
    ].join(' · ');
    return ListView(
      padding: const EdgeInsets.only(bottom: 24),
      children: [
        _BlokIdentitas(pasien, keterangan: keterangan),
        _PanelLevel(detail),
        const SizedBox(height: 10),
        KartuBagian(
          judul: 'Skor NEWS2: ${penjelasan.skorNews2}',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              if (penjelasan.komponenNews2.isEmpty)
                const Text('Semua parameter NEWS2 dalam batas normal.', style: TextStyle(color: Warna.teksRedup))
              else
                for (final k in penjelasan.komponenNews2) _BarisPoin(k.label, k.kontribusi.round()),
              const SizedBox(height: 6),
              Text(
                'Level menurut NEWS2: ${labelLevel(penjelasan.levelNews2)}',
                style: const TextStyle(color: Warna.teksRedup, fontSize: 14),
              ),
            ],
          ),
        ),
        if (faktor.isNotEmpty) ...[
          const SizedBox(height: 10),
          KartuBagian(
            judul: 'Faktor yang paling memengaruhi peluang memburuk',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                for (final (i, f) in faktor.indexed)
                  _BarisFaktor(
                    f,
                    porsi: kontribusiMaks == 0 ? 0.0 : f.kontribusi.abs() / kontribusiMaks,
                    pertama: i == 0,
                  ),
              ],
            ),
          ),
        ],
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
              _KisiTandaVital(detail.tandaVital, oksigen: detail.oksigenTambahan),
              const SizedBox(height: 8),
              _BarisData('Sumber tanda vital', labelSumberTandaVital(detail.sumberTandaVital)),
            ],
          ),
        ),
        const SizedBox(height: 10),
        KartuBagian(
          judul: 'Hasil lab dan alat bantu',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _BarisData('Hasil lab', _teksLab(detail)),
              _BarisData(
                'Alat bantu',
                detail.ventilator || detail.vasopresor
                    ? [if (detail.ventilator) 'Ventilator', if (detail.vasopresor) 'Vasopresor'].join(', ')
                    : 'Tidak ada',
              ),
            ],
          ),
        ),
        const SizedBox(height: 10),
        KartuBagian(
          judul: 'Data observasi',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _BarisData('Kesadaran', labelKesadaran(detail.tingkatKesadaran)),
              if (detail.catatan != null) _BarisData('Catatan perawat', detail.catatan!),
              _BarisData('Diinput oleh', detail.dibuatOleh.nama),
              if (detail.divalidasiOleh != null) _BarisData('Divalidasi oleh', detail.divalidasiOleh!.nama),
              if (detail.catatanValidasiTerakhir != null)
                _BarisData('Alasan review atau koreksi', detail.catatanValidasiTerakhir!),
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

  /// Pesan status dan tindakan lain di bawah data observasi. Tombol keputusan ada di [_tombolKeputusan].
  List<Widget> _aksi(TriaseDetail detail, Peran? peran) {
    final status = detail.statusValidasi;
    final statusKunjungan = _statusKunjungan;
    final diIcu = statusKunjungan != null && statusKunjungan != StatusKunjungan.selesai;
    final aksi = <Widget>[];
    void tambah(Widget tombol) => aksi.addAll([tombol, const SizedBox(height: 10)]);

    if (peran == Peran.perawat && status == StatusValidasi.menunggu) {
      tambah(
        KotakPesan(
          detail.jenis == JenisTriase.awal
              ? 'Penilaian awal ini perlu disetujui dokter. Sampaikan ke dokter jaga, atau ajukan review.'
              : 'Level pasien naik dan perlu disetujui dokter. Sampaikan ke dokter jaga, atau ajukan review.',
          jenis: detail.riskLevel == RiskLevel.kritis ? JenisPesan.galat : JenisPesan.peringatan,
        ),
      );
    } else if (peran == Peran.perawat && status == StatusValidasi.menungguReviewDokter) {
      tambah(const KotakPesan('Review sudah diajukan ke dokter.', jenis: JenisPesan.info));
    }
    if (peran == Peran.dokter && diIcu) {
      final dirawat = statusKunjungan == StatusKunjungan.menunggu;
      tambah(
        OutlinedButton.icon(
          onPressed: _sibuk
              ? null
              : () => _ubahStatus(
                  detail.idKunjungan,
                  dirawat ? StatusKunjunganRequestStatus.ditangani : StatusKunjunganRequestStatus.menunggu,
                ),
          icon: Icon(dirawat ? Icons.medical_services_outlined : Icons.monitor_heart_outlined),
          label: Text(dirawat ? 'Mulai tindakan atau operasi' : 'Selesai tindakan, kembali dipantau'),
        ),
      );
      tambah(
        OutlinedButton.icon(
          onPressed: _sibuk ? null : () => _keluarIcu(detail.idKunjungan),
          icon: const Icon(Icons.logout),
          label: const Text('Pasien keluar ICU'),
        ),
      );
    }
    if (peran == Peran.perawat && diIcu) {
      tambah(
        OutlinedButton.icon(
          onPressed: () => context.push(
            Rute.formTriase(detail.idKunjungan),
            extra: InfoFormTriase(pasien: detail.pasien, nomorBed: detail.nomorBed, triaseUlang: true),
          ),
          icon: const Icon(Icons.edit_note),
          label: const Text('Observasi baru'),
        ),
      );
      tambah(
        OutlinedButton.icon(
          onPressed: () => context.push(Rute.kodeQrEir(detail.idKunjungan), extra: detail.pasien),
          icon: const Icon(Icons.qr_code_2),
          label: const Text('Kode QR Eir untuk keluarga'),
        ),
      );
    }
    tambah(
      TextButton.icon(
        onPressed: () => context.push(Rute.riwayatPasien(detail.pasien.idPasien), extra: detail.pasien),
        icon: const Icon(Icons.history),
        label: const Text('Riwayat observasi pasien'),
      ),
    );
    return aksi;
  }

  String _teksLab(TriaseDetail detail) {
    final lab = detail.lab;
    final nilai = {
      'laktat': lab.laktat,
      'kreatinin': lab.kreatinin,
      'trombosit': lab.trombosit,
      'leukosit': lab.leukosit,
      'bilirubin': lab.bilirubin,
    };
    final isi = [
      for (final MapEntry(key: kolom, value: angkaLab) in nilai.entries)
        if (angkaLab != null)
          '${kolomLab[kolom]!.$1} ${_angkaLab(angkaLab, kolomLab[kolom]!.$3)} ${kolomLab[kolom]!.$2}',
    ];
    return isi.isEmpty ? 'Tidak diisi' : isi.join('\n');
  }

  String _angkaLab(num nilai, int desimal) {
    if (desimal < 2 || nilai == nilai.roundToDouble()) return angka(nilai);
    return nilai.toStringAsFixed(2).replaceAll('.', ',');
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

/// Level prioritas dengan garis warna level di kiri, perubahan level, dasar penilaian, dan status persetujuan.
class _PanelLevel extends StatelessWidget {
  const _PanelLevel(this.detail);

  final TriaseDetail detail;

  static const _urutan = [RiskLevel.rendah, RiskLevel.sedang, RiskLevel.tinggi, RiskLevel.kritis];

  static bool _naik(RiskLevel dari, RiskLevel ke) => _urutan.indexOf(ke) > _urutan.indexOf(dari);

  @override
  Widget build(BuildContext context) {
    final sebelumnya = detail.levelSebelumnya;
    final penjelasan = detail.penjelasanAi;
    final peluang = penjelasan.peluangPerburukan;
    final levelModel = penjelasan.levelModel;
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
            'Prioritas penanganan',
            style: TextStyle(color: Warna.teksRedup, fontSize: 14, fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 6),
          LencanaRisiko(detail.riskLevel, besar: true),
          if (sebelumnya != null && sebelumnya != detail.riskLevel) ...[
            const SizedBox(height: 6),
            Text(
              '${_naik(sebelumnya, detail.riskLevel) ? 'Naik' : 'Turun'} dari ${labelLevel(sebelumnya)}',
              style: TextStyle(
                fontWeight: FontWeight.w700,
                color: _naik(sebelumnya, detail.riskLevel) ? Warna.galat : Warna.teksRedup,
              ),
            ),
          ],
          const SizedBox(height: 8),
          Text(
            [
              'NEWS2 ${penjelasan.skorNews2} (${labelLevel(penjelasan.levelNews2).toLowerCase()})',
              if (peluang != null && levelModel != null)
                'peluang memburuk 6 jam ${persenPeluang(peluang)} (${labelLevel(levelModel).toLowerCase()})',
            ].join(' · '),
            style: const TextStyle(fontSize: 15),
          ),
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
                'Model AI sedang tidak tersedia, jadi level dihitung dari skor NEWS2 dengan ambang yang diatur admin.',
                jenis: JenisPesan.peringatan,
              ),
            ),
          const SizedBox(height: 8),
          const Text(
            'Level diambil dari yang lebih tinggi antara NEWS2 dan model. Ini rekomendasi urutan penanganan; '
            'keputusan tetap di tangan dokter.',
            style: TextStyle(color: Warna.teksSamar, fontSize: 13),
          ),
        ],
      ),
    );
  }
}

/// Enam tanda vital dan status oksigen dalam kisi tiga kolom, angka besar dan satuan kecil.
class _KisiTandaVital extends StatelessWidget {
  const _KisiTandaVital(this.tv, {required this.oksigen});

  final TandaVitalResponse tv;
  final bool oksigen;

  @override
  Widget build(BuildContext context) {
    final sel = [
      ('Tekanan darah', '${tv.tdSistolik}/${tv.tdDiastolik}', 'mmHg'),
      ('Nadi', '${tv.nadi}', 'x/mnt'),
      ('Napas', '${tv.lajuNapas}', 'x/mnt'),
      ('Suhu', angka(tv.suhu), '°C'),
      ('SpO₂', angka(tv.saturasi), '%'),
      ('Oksigen', oksigen ? 'Ya' : 'Tidak', ''),
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
      StatusValidasi.tercatat => (Warna.teksRedup, Icons.check_circle_outline),
      _ => (Warna.waspada, Icons.pending_actions),
    };
    return Tanda(labelStatusValidasi(status), warna: warna, ikon: ikon);
  }
}

/// Satu komponen NEWS2 dan poinnya.
class _BarisPoin extends StatelessWidget {
  const _BarisPoin(this.label, this.poin);

  final String label;
  final int poin;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Expanded(child: Text(label, style: const TextStyle(fontSize: 15))),
          Text(
            '+$poin',
            style: TextStyle(fontWeight: FontWeight.w700, color: poin >= 3 ? Warna.galat : Warna.teks),
          ),
        ],
      ),
    );
  }
}

/// Satu faktor penjelas: nama dan nilainya, arah pengaruh, dan batang sepanjang besar pengaruh dibanding faktor
/// terbesar. Warnanya netral karena warna merah sampai hijau khusus untuk level risiko.
class _BarisFaktor extends StatelessWidget {
  const _BarisFaktor(this.faktor, {required this.porsi, required this.pertama});

  final FaktorResponse faktor;
  final double porsi;
  final bool pertama;

  @override
  Widget build(BuildContext context) {
    final (ikon, keterangan) = switch (faktor.arah) {
      FaktorResponseArah.naik => (Icons.arrow_upward, 'menaikkan peluang memburuk'),
      FaktorResponseArah.turun => (Icons.arrow_downward, 'menurunkan peluang memburuk'),
      _ => (Icons.remove, 'tidak berpengaruh'),
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
          Text(faktor.label, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
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
      title: const Text('Koreksi level prioritas'),
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
