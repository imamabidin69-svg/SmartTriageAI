import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../api/galat_api.dart';
import '../api/generated/models/jenis_alat.dart';
import '../api/generated/models/kategori_keluhan.dart';
import '../api/generated/models/pengisi_eir.dart';
import '../api/generated/models/status_kunjungan.dart';
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

/// Form Triase (SKPL Tabel 7.1 no. 4, mockup Gambar 7.1): keluhan, kesadaran, skala nyeri, dan tanda vital,
/// termasuk tombol Pindai layar alat. Hitung rekomendasi membuka halaman Hasil dan Penjelasan.
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
  final _nyeri = TextEditingController();
  final _keluhan = TextEditingController();
  final _gejala = TextEditingController();
  TingkatKesadaran? _kesadaran;
  KategoriKeluhan? _kategori;

  /// Kolom yang angkanya dari foto: alat dan nilai terbaca. Bila perawat mengubah angkanya, tanda dihapus.
  final _dariFoto = <String, (JenisAlat, String)>{};
  final _idPemindaian = <String>[];
  String? _sumberEir;

  bool _sibuk = false;
  bool _memuatEir = false;
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
    for (final pengendali in [..._tandaVital.values, _nyeri, _keluhan, _gejala]) {
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

  Future<void> _isiDariEir() async {
    setState(() => _memuatEir = true);
    try {
      final eir = await ref.read(repositoriProvider).ringkasanEir(widget.idKunjungan);
      final ringkasan = eir.ringkasan;
      if (!mounted) return;
      if (ringkasan == null) {
        tampilkanPesan(context, 'Percakapan Eir belum selesai, jadi ringkasannya belum ada.');
        return;
      }
      setState(() {
        _keluhan.text = ringkasan.keluhanUtama;
        _gejala.text = ringkasan.onset.trim().isEmpty
            ? ringkasan.gejala
            : '${ringkasan.gejala}\nSejak: ${ringkasan.onset}';
        if (ringkasan.kategoriKeluhan != KategoriKeluhan.$unknown) _kategori = ringkasan.kategoriKeluhan;
        _sumberEir = eir.pengisi == PengisiEir.keluarga ? 'keluarga pasien' : 'pasien';
      });
    } on GalatApi catch (galat) {
      if (mounted) tampilkanPesan(context, galat.pesan, galat: true);
    } finally {
      if (mounted) setState(() => _memuatEir = false);
    }
  }

  Future<void> _hitung() async {
    setState(() => _sudahDicoba = true);
    final formValid = _form.currentState!.validate();
    if (!formValid || _kesadaran == null || _kategori == null) return;
    setState(() {
      _sibuk = true;
      _galat = null;
    });
    final nilai = {for (final MapEntry(:key, :value) in _tandaVital.entries) key: bacaAngka(value.text)!};
    final data = TriaseInput(
      keluhanUtama: _keluhan.text.trim(),
      gejala: _gejala.text.trim(),
      kategoriKeluhan: _kategori!,
      skalaNyeri: int.parse(_nyeri.text.trim()),
      tingkatKesadaran: _kesadaran!,
      tandaVital: TandaVital(
        tdSistolik: nilai['td_sistolik']!.toInt(),
        tdDiastolik: nilai['td_diastolik']!.toInt(),
        nadi: nilai['nadi']!.toInt(),
        lajuNapas: nilai['laju_napas']!.toInt(),
        suhu: nilai['suhu']!,
        saturasi: nilai['saturasi']!,
      ),
      idPemindaian: List.of(_idPemindaian),
    );
    try {
      final detail = await ref.read(repositoriProvider).buatTriase(widget.idKunjungan, data);
      if (!mounted) return;
      unawaited(ref.read(antreanProvider.notifier).muatUlang());
      context.pushReplacement(
        Rute.hasil(detail.idTriase),
        extra: InfoHasil(detail: detail, statusKunjungan: StatusKunjungan.menunggu),
      );
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
    return Scaffold(
      appBar: AppBar(title: const Text('Form Triase')),
      body: Form(
        key: _form,
        autovalidateMode: _sudahDicoba ? AutovalidateMode.onUserInteraction : AutovalidateMode.disabled,
        child: ListView(
          controller: _gulir,
          padding: const EdgeInsets.all(16),
          children: [
            Text(
              info?.triaseUlang == true ? 'Triase ulang' : 'Triase',
              style: const TextStyle(color: Warna.teksRedup, fontSize: 15),
            ),
            if (pasien != null) ...[
              Text(pasien.nama, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w700)),
              Text(
                [
                  if (pasien.usia != null) '${pasien.usia} th',
                  labelKelamin(pasien.jenisKelamin),
                  if (waktuDatang != null) 'datang ${jamWib(waktuDatang)}',
                ].join(' · '),
                style: const TextStyle(color: Warna.teksRedup, fontSize: 16),
              ),
            ],
            const SizedBox(height: 16),
            if (pesanUmum != null) ...[KotakPesan(pesanUmum), const SizedBox(height: 12)],
            _kartuTandaVital(),
            const SizedBox(height: 16),
            _kartuKeluhan(),
            const SizedBox(height: 20),
            TombolProses(label: 'Hitung rekomendasi', sibuk: _sibuk, onPressed: _hitung),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }

  Widget _kartuTandaVital() {
    final jumlahFoto = _dariFoto.length;
    return KartuBagian(
      judul: 'Tanda vital',
      aksi: FilledButton.icon(
        style: FilledButton.styleFrom(minimumSize: const Size(48, 44)),
        onPressed: _sibuk ? null : _pindai,
        icon: const Icon(Icons.photo_camera_outlined),
        label: const Text('Pindai layar alat'),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (jumlahFoto > 0) ...[
            KotakPesan('$jumlahFoto nilai dibaca dari foto. Periksa sebelum menyimpan.', jenis: JenisPesan.peringatan),
            const SizedBox(height: 12),
          ],
          LayoutBuilder(
            builder: (context, batas) {
              final lebar = (batas.maxWidth - 12) / 2;
              return Wrap(
                spacing: 12,
                runSpacing: 4,
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
    final kuning = asal != null
        ? OutlineInputBorder(
            borderRadius: BorderRadius.circular(10),
            borderSide: const BorderSide(color: Color(0xFFF59E0B), width: 1.5),
          )
        : null;
    return TextFormField(
      key: ValueKey('tanda-vital-$kolom'),
      controller: _tandaVital[kolom],
      keyboardType: TextInputType.numberWithOptions(decimal: desimal),
      inputFormatters: [FilteringTextInputFormatter.allow(RegExp(desimal ? r'[0-9.,]' : r'[0-9]'))],
      textInputAction: TextInputAction.next,
      decoration: InputDecoration(
        labelText: labelTandaVital[kolom],
        hintText: 'isi manual',
        filled: true,
        fillColor: asal != null ? const Color(0xFFFFFBEB) : Colors.white,
        enabledBorder: kuning,
        helperText: asal == null ? ' ' : 'dari ${labelAlat(asal.$1).toLowerCase()}',
        helperStyle: const TextStyle(color: Warna.peringatan),
        errorText: _galat?.field('tanda_vital.$kolom'),
      ),
      validator: (teks) => periksaTandaVital(kolom, teks ?? ''),
    );
  }

  Widget _kartuKeluhan() {
    final galat = _galat;
    final kesadaranKosong = _sudahDicoba && _kesadaran == null;
    final kategoriKosong = _sudahDicoba && _kategori == null;
    return KartuBagian(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (widget.info?.ringkasanEirSiap == true || _sumberEir != null) ...[
            if (_sumberEir == null)
              OutlinedButton.icon(
                onPressed: _memuatEir ? null : _isiDariEir,
                icon: const Icon(Icons.chat_outlined),
                label: Text(_memuatEir ? 'Memuat ringkasan Eir...' : 'Isi dari ringkasan Eir'),
              )
            else
              KotakPesan(
                'Keluhan dan gejala diisi dari ringkasan Eir yang dijawab $_sumberEir. Periksa dan lengkapi sebelum '
                'menghitung rekomendasi.',
                jenis: JenisPesan.info,
              ),
            const SizedBox(height: 16),
          ],
          const Text('Kesadaran (AVPU)', style: TextStyle(fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          SegmentedButton<TingkatKesadaran>(
            segments: [
              for (final tingkat in TingkatKesadaran.$valuesDefined)
                ButtonSegment(value: tingkat, label: Text(tingkat.json!), tooltip: labelKesadaran(tingkat)),
            ],
            selected: {?_kesadaran},
            emptySelectionAllowed: true,
            showSelectedIcon: false,
            onSelectionChanged: (pilihan) => setState(() => _kesadaran = pilihan.firstOrNull),
          ),
          if (kesadaranKosong || galat?.field('tingkat_kesadaran') != null)
            Padding(
              padding: const EdgeInsets.only(top: 6),
              child: Text(
                galat?.field('tingkat_kesadaran') ?? 'Pilih tingkat kesadaran.',
                style: const TextStyle(color: Warna.galat, fontSize: 12),
              ),
            ),
          const SizedBox(height: 16),
          TextFormField(
            key: const ValueKey('skala-nyeri'),
            controller: _nyeri,
            keyboardType: TextInputType.number,
            inputFormatters: [FilteringTextInputFormatter.digitsOnly],
            decoration: InputDecoration(labelText: 'Skala nyeri (0-10)', errorText: galat?.field('skala_nyeri')),
            validator: (teks) => periksaSkalaNyeri(teks ?? ''),
          ),
          const SizedBox(height: 16),
          DropdownButtonFormField<KategoriKeluhan>(
            key: const ValueKey('kategori-keluhan'),
            initialValue: _kategori,
            isExpanded: true,
            decoration: InputDecoration(
              labelText: 'Kategori keluhan',
              errorText: galat?.field('kategori_keluhan') ?? (kategoriKosong ? 'Pilih kategori keluhan.' : null),
            ),
            items: [
              for (final kategori in KategoriKeluhan.$valuesDefined)
                DropdownMenuItem(
                  value: kategori,
                  child: Text(kategori.json!, overflow: TextOverflow.ellipsis),
                ),
            ],
            onChanged: (kategori) => setState(() => _kategori = kategori),
          ),
          const SizedBox(height: 16),
          TextFormField(
            key: const ValueKey('keluhan-utama'),
            controller: _keluhan,
            maxLength: 200,
            decoration: InputDecoration(labelText: 'Keluhan utama', errorText: galat?.field('keluhan_utama')),
            validator: (teks) => periksaPanjang(teks ?? '', min: 1, maks: 200, nama: 'Keluhan utama'),
          ),
          const SizedBox(height: 8),
          TextFormField(
            key: const ValueKey('gejala'),
            controller: _gejala,
            minLines: 3,
            maxLines: 6,
            maxLength: 2000,
            decoration: InputDecoration(
              labelText: 'Gejala',
              alignLabelWithHint: true,
              hintText: 'Gejala penyerta, sejak kapan, dan hal lain yang dikeluhkan',
              errorText: galat?.field('gejala'),
            ),
            validator: (teks) => periksaPanjang(teks ?? '', min: 10, maks: 2000, nama: 'Gejala'),
          ),
        ],
      ),
    );
  }
}
