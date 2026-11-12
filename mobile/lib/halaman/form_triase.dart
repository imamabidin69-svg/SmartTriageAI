import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../api/galat_api.dart';
import '../api/generated/models/hasil_lab.dart';
import '../api/generated/models/jenis_alat.dart';
import '../api/generated/models/tanda_vital.dart';
import '../api/generated/models/tingkat_kesadaran.dart';
import '../api/generated/models/triase_input.dart';
import '../komponen/umum.dart';
import '../rute.dart';
import '../state/antrean.dart';
import '../state/penyedia.dart';
import '../tema.dart';
import '../util/format.dart';
import '../util/label.dart';
import '../util/validasi.dart';
import 'pemindaian.dart';

/// Form Observasi ICU (pengganti Form Triase SKPL Tabel 7.1 no. 4): tanda vital (bisa dipindai dari bedside
/// monitor), kesadaran AVPU, oksigen tambahan, hasil lab opsional, alat bantu, dan catatan. Tombol Nilai prioritas
/// mengirim observasi lalu membuka Hasil Penilaian.
class HalamanFormTriase extends ConsumerStatefulWidget {
  const HalamanFormTriase({super.key, required this.idKunjungan, this.info});

  final String idKunjungan;
  final InfoFormTriase? info;

  @override
  ConsumerState<HalamanFormTriase> createState() => _HalamanFormTriaseState();
}

class _HalamanFormTriaseState extends ConsumerState<HalamanFormTriase> {
  final _form = GlobalKey<FormState>();
  final _gulir = ScrollController();
  final _tandaVital = {for (final kolom in urutanTandaVital) kolom: TextEditingController()};
  final _lab = {for (final kolom in kolomLab.keys) kolom: TextEditingController()};
  final _catatan = TextEditingController();
  TingkatKesadaran? _kesadaran;
  bool? _oksigen;
  bool _ventilator = false;
  bool _vasopresor = false;

  /// Kolom yang angkanya dari foto: alat dan nilai terbaca. Bila perawat mengubah angkanya, tanda dihapus.
  final _dariFoto = <String, (JenisAlat, String)>{};
  final _idPemindaian = <String>[];

  bool _sibuk = false;
  bool _sudahDicoba = false;
  GalatApi? _galat;

  @override
  void initState() {
    super.initState();
    for (final MapEntry(key: kolom, value: pengendali) in _tandaVital.entries) {
      pengendali.addListener(() {
        final asal = _dariFoto[kolom];
        if (asal != null && asal.$2 != pengendali.text) setState(() => _dariFoto.remove(kolom));
      });
    }
  }

  @override
  void dispose() {
    for (final pengendali in [..._tandaVital.values, ..._lab.values, _catatan]) {
      pengendali.dispose();
    }
    _gulir.dispose();
    super.dispose();
  }

  Future<void> _pindai() async {
    final hasil = await context.push<HasilPindai>(Rute.pemindaian);
    if (hasil == null || !mounted) return;
    setState(() {
      for (final MapEntry(key: kolom, value: nilai) in hasil.nilai.entries) {
        final pengendali = _tandaVital[kolom];
        if (pengendali == null) continue;
        final teks = angka(nilai);
        _dariFoto[kolom] = (hasil.alat, teks);
        pengendali.text = teks;
      }
      if (!_idPemindaian.contains(hasil.idPemindaian) && _idPemindaian.length < 4) {
        _idPemindaian.add(hasil.idPemindaian);
      }
    });
  }

  HasilLab _hasilLab() {
    num? baca(String kolom) => bacaAngka(_lab[kolom]!.text);
    return HasilLab(
      laktat: baca('laktat'),
      kreatinin: baca('kreatinin'),
      trombosit: baca('trombosit')?.toInt(),
      leukosit: baca('leukosit'),
      bilirubin: baca('bilirubin'),
    );
  }

  Future<void> _kirim() async {
    setState(() => _sudahDicoba = true);
    final formValid = _form.currentState!.validate();
    if (!formValid || _kesadaran == null || _oksigen == null) return;
    setState(() {
      _sibuk = true;
      _galat = null;
    });
    final nilai = {for (final MapEntry(:key, :value) in _tandaVital.entries) key: bacaAngka(value.text)!};
    final catatan = _catatan.text.trim();
    final data = TriaseInput(
      tingkatKesadaran: _kesadaran!,
      oksigenTambahan: _oksigen!,
      tandaVital: TandaVital(
        tdSistolik: nilai['td_sistolik']!.toInt(),
        tdDiastolik: nilai['td_diastolik']!.toInt(),
        nadi: nilai['nadi']!.toInt(),
        lajuNapas: nilai['laju_napas']!.toInt(),
        suhu: nilai['suhu']!,
        saturasi: nilai['saturasi']!,
      ),
      lab: _hasilLab(),
      ventilator: _ventilator,
      vasopresor: _vasopresor,
      catatan: catatan.isEmpty ? null : catatan,
      idPemindaian: List.of(_idPemindaian),
    );
    try {
      final detail = await ref.read(repositoriProvider).buatTriase(widget.idKunjungan, data);
      if (!mounted) return;
      unawaited(ref.read(antreanProvider.notifier).muatUlang());
      context.pushReplacement(Rute.hasil(detail.idTriase), extra: InfoHasil(detail: detail));
    } on GalatApi catch (galat) {
      if (!mounted) return;
      setState(() => _galat = galat);
      // Pesan error ada di atas form, sedangkan perawat sedang di tombol paling bawah.
      if (_gulir.hasClients) {
        unawaited(_gulir.animateTo(0, duration: const Duration(milliseconds: 300), curve: Curves.easeOut));
      }
    } finally {
      if (mounted) setState(() => _sibuk = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final info = widget.info;
    final pasien = info?.pasien;
    final galat = _galat;
    final pesanUmum = galat == null
        ? null
        : galat.pesanField.isEmpty
        ? galat.pesan
        : 'Periksa kembali kolom yang ditandai merah.';
    final waktuDatang = info?.waktuDatang;
    final ulang = info?.triaseUlang == true;
    return Scaffold(
      appBar: AppBar(title: Text(ulang ? 'Observasi Pasien' : 'Penilaian Awal')),
      body: Form(
        key: _form,
        autovalidateMode: _sudahDicoba ? AutovalidateMode.onUserInteraction : AutovalidateMode.disabled,
        child: ListView(
          controller: _gulir,
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
                    Text(
                      [
                        ulang ? 'Observasi' : 'Penilaian awal',
                        if (info?.nomorBed != null) 'Bed ${info!.nomorBed}',
                      ].join(' · '),
                      style: const TextStyle(color: Warna.teksRedup, fontSize: 14, fontWeight: FontWeight.w700),
                    ),
                    if (pasien != null) ...[
                      Text(pasien.nama, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700)),
                      Text(
                        [
                          if (pasien.usia != null) '${pasien.usia} th',
                          labelKelamin(pasien.jenisKelamin),
                          if (waktuDatang != null) 'masuk ${jamWib(waktuDatang)}',
                        ].join(' · '),
                        style: const TextStyle(color: Warna.teksRedup, fontSize: 15),
                      ),
                    ],
                  ],
                ),
              ),
            ),
            if (info?.ringkasanEirSiap == true) _barisEir(pasien?.nama),
            if (pesanUmum != null)
              Padding(padding: const EdgeInsets.fromLTRB(16, 12, 16, 0), child: KotakPesan(pesanUmum)),
            const SizedBox(height: 12),
            _kartuTandaVital(),
            const SizedBox(height: 12),
            _kartuKesadaranOksigen(),
            const SizedBox(height: 12),
            _kartuLab(),
            const SizedBox(height: 12),
            _kartuAlatBantu(),
          ],
        ),
      ),
      // Tombol simpan selalu terlihat, jadi perawat tidak perlu menggulir ke akhir form.
      bottomNavigationBar: BilahBawah(
        tombol: [TombolProses(label: 'Nilai prioritas', sibuk: _sibuk, onPressed: _kirim)],
      ),
    );
  }

  /// Pemberitahuan bahwa keluarga sudah menjawab Eir, dengan tombol untuk membaca ringkasan riwayatnya.
  Widget _barisEir(String? namaPasien) {
    return DecoratedBox(
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(bottom: BorderSide(color: Warna.garis)),
      ),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.description_outlined, color: Warna.utama),
                SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Ringkasan Eir dari keluarga sudah masuk', style: TextStyle(fontWeight: FontWeight.w700)),
                      Text(
                        'Berisi riwayat penyakit, obat rutin, dan alergi pasien.',
                        style: TextStyle(color: Warna.teksRedup, fontSize: 14),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            Align(
              alignment: Alignment.centerRight,
              child: TextButton(
                onPressed: () => context.push(Rute.ringkasanEir(widget.idKunjungan), extra: namaPasien),
                child: const Text('Baca ringkasan Eir'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _kartuTandaVital() {
    final jumlahFoto = _dariFoto.length;
    return KartuBagian(
      judul: 'Tanda vital',
      aksi: OutlinedButton.icon(
        style: OutlinedButton.styleFrom(
          minimumSize: const Size(48, 40),
          padding: const EdgeInsets.symmetric(horizontal: 12),
          textStyle: const TextStyle(fontFamily: hurufAplikasi, fontSize: 14, fontWeight: FontWeight.w700),
        ),
        onPressed: _sibuk ? null : _pindai,
        icon: const Icon(Icons.photo_camera_outlined, size: 20),
        label: const Text('Pindai monitor'),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (jumlahFoto > 0) ...[
            KotakPesan('$jumlahFoto nilai dibaca dari foto. Periksa sebelum menyimpan.', jenis: JenisPesan.info),
            const SizedBox(height: 14),
          ],
          LayoutBuilder(
            builder: (context, batas) {
              final lebar = (batas.maxWidth - 12) / 2;
              return Wrap(
                spacing: 12,
                runSpacing: 6,
                children: [
                  for (final kolom in urutanTandaVital) SizedBox(width: lebar, child: _kolomTandaVital(kolom)),
                ],
              );
            },
          ),
        ],
      ),
    );
  }

  Widget _kolomTandaVital(String kolom) {
    final asal = _dariFoto[kolom];
    final desimal = kolomDesimal.contains(kolom);
    // Nilai dari foto diberi latar biru muda dan keterangan alatnya, sampai perawat mengubah angkanya.
    final biru = asal != null
        ? OutlineInputBorder(
            borderRadius: BorderRadius.circular(6),
            borderSide: const BorderSide(color: Warna.utamaGaris, width: 1.5),
          )
        : null;
    return TextFormField(
      key: ValueKey('tanda-vital-$kolom'),
      controller: _tandaVital[kolom],
      keyboardType: TextInputType.numberWithOptions(decimal: desimal),
      inputFormatters: [FilteringTextInputFormatter.allow(RegExp(desimal ? r'[0-9.,]' : r'[0-9]'))],
      textInputAction: TextInputAction.next,
      style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w600),
      decoration: InputDecoration(
        labelText: labelPendekTandaVital[kolom],
        suffixText: satuanTandaVital[kolom],
        fillColor: asal != null ? Warna.utamaMuda : Colors.white,
        enabledBorder: biru,
        helperText: asal == null ? ' ' : 'dari ${labelAlat(asal.$1).toLowerCase()}',
        helperStyle: const TextStyle(color: Warna.utama, fontWeight: FontWeight.w700),
        errorText: _galat?.field('tanda_vital.$kolom'),
        errorMaxLines: 2,
      ),
      validator: (teks) => periksaTandaVital(kolom, teks ?? ''),
    );
  }

  Widget _pesanWajib(String? pesan) => Padding(
    padding: const EdgeInsets.only(top: 6),
    child: Text(
      pesan ?? '',
      style: const TextStyle(color: Warna.galat, fontSize: 13, fontWeight: FontWeight.w600),
    ),
  );

  Widget _kartuKesadaranOksigen() {
    final galat = _galat;
    final kesadaranKosong = _sudahDicoba && _kesadaran == null;
    final oksigenKosong = _sudahDicoba && _oksigen == null;
    return KartuBagian(
      judul: 'Kesadaran dan oksigen',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text('Tingkat kesadaran (AVPU)', style: TextStyle(fontWeight: FontWeight.w700)),
          const SizedBox(height: 8),
          SegmentedButton<TingkatKesadaran>(
            style: const ButtonStyle(
              minimumSize: WidgetStatePropertyAll(Size(48, 56)),
              padding: WidgetStatePropertyAll(EdgeInsets.symmetric(horizontal: 4)),
            ),
            segments: [
              for (final tingkat in TingkatKesadaran.$valuesDefined)
                ButtonSegment(
                  value: tingkat,
                  tooltip: labelKesadaran(tingkat),
                  label: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(tingkat.json!),
                      // Satu baris untuk semua pilihan; teks terpanjang diperkecil sedikit bila tidak muat.
                      FittedBox(
                        fit: BoxFit.scaleDown,
                        child: Text(
                          singkatanKesadaran(tingkat),
                          maxLines: 1,
                          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w400),
                        ),
                      ),
                    ],
                  ),
                ),
            ],
            selected: {?_kesadaran},
            emptySelectionAllowed: true,
            showSelectedIcon: false,
            onSelectionChanged: (pilihan) => setState(() => _kesadaran = pilihan.firstOrNull),
          ),
          if (kesadaranKosong || galat?.field('tingkat_kesadaran') != null)
            _pesanWajib(galat?.field('tingkat_kesadaran') ?? 'Pilih tingkat kesadaran.'),
          const SizedBox(height: 20),
          const Text('Oksigen tambahan', style: TextStyle(fontWeight: FontWeight.w700)),
          const Text(
            'Nasal kanul, masker, HFNC, atau ventilator. Menambah 2 poin NEWS2.',
            style: TextStyle(color: Warna.teksRedup, fontSize: 13),
          ),
          const SizedBox(height: 8),
          SegmentedButton<bool>(
            style: const ButtonStyle(minimumSize: WidgetStatePropertyAll(Size(48, 48))),
            segments: const [
              ButtonSegment(value: false, label: Text('Udara ruangan')),
              ButtonSegment(value: true, label: Text('Ya, oksigen')),
            ],
            selected: {?_oksigen},
            emptySelectionAllowed: true,
            showSelectedIcon: false,
            onSelectionChanged: (pilihan) => setState(() => _oksigen = pilihan.firstOrNull),
          ),
          if (oksigenKosong || galat?.field('oksigen_tambahan') != null)
            _pesanWajib(galat?.field('oksigen_tambahan') ?? 'Pilih apakah pasien mendapat oksigen tambahan.'),
        ],
      ),
    );
  }

  Widget _kartuLab() {
    return KartuBagian(
      judul: 'Hasil lab terakhir (opsional)',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text(
            'Isi bila ada. Kolom yang kosong tidak dipakai sebagai faktor penjelas.',
            style: TextStyle(color: Warna.teksRedup, fontSize: 13),
          ),
          const SizedBox(height: 12),
          LayoutBuilder(
            builder: (context, batas) {
              final lebar = (batas.maxWidth - 12) / 2;
              return Wrap(
                spacing: 12,
                runSpacing: 6,
                children: [
                  for (final MapEntry(key: kolom, value: (label, satuan, desimal)) in kolomLab.entries)
                    SizedBox(
                      width: lebar,
                      child: TextFormField(
                        key: ValueKey('lab-$kolom'),
                        controller: _lab[kolom],
                        keyboardType: TextInputType.numberWithOptions(decimal: desimal > 0),
                        inputFormatters: [
                          FilteringTextInputFormatter.allow(RegExp(desimal > 0 ? r'[0-9.,]' : r'[0-9]')),
                        ],
                        textInputAction: TextInputAction.next,
                        style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w600),
                        decoration: InputDecoration(
                          labelText: label,
                          suffixText: satuan,
                          helperText: ' ',
                          errorText: _galat?.field('lab.$kolom'),
                          errorMaxLines: 2,
                        ),
                        validator: (teks) => periksaLab(kolom, teks ?? ''),
                      ),
                    ),
                ],
              );
            },
          ),
        ],
      ),
    );
  }

  Widget _kartuAlatBantu() {
    return KartuBagian(
      judul: 'Alat bantu dan catatan',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          SwitchListTile(
            key: const ValueKey('ventilator'),
            contentPadding: EdgeInsets.zero,
            title: const Text('Memakai ventilator'),
            value: _ventilator,
            onChanged: (nilai) => setState(() => _ventilator = nilai),
          ),
          SwitchListTile(
            key: const ValueKey('vasopresor'),
            contentPadding: EdgeInsets.zero,
            title: const Text('Mendapat vasopresor'),
            value: _vasopresor,
            onChanged: (nilai) => setState(() => _vasopresor = nilai),
          ),
          const SizedBox(height: 8),
          TextFormField(
            key: const ValueKey('catatan'),
            controller: _catatan,
            minLines: 2,
            maxLines: 5,
            maxLength: 500,
            decoration: InputDecoration(
              labelText: 'Catatan (opsional)',
              alignLabelWithHint: true,
              hintText: 'Misalnya produksi urin, keluhan baru, atau tindakan yang baru diberikan',
              errorText: _galat?.field('catatan'),
            ),
          ),
        ],
      ),
    );
  }
}
