import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../api/galat_api.dart';
import '../api/generated/models/jenis_kelamin.dart';
import '../api/generated/models/kunjungan_dibuat_response.dart';
import '../api/generated/models/pasien_ringkas.dart';
import '../api/generated/models/pasien_triase.dart';
import '../api/generated/models/registrasi_request.dart';
import '../komponen/umum.dart';
import '../rute.dart';
import '../state/antrean.dart';
import '../state/penyedia.dart';
import '../tema.dart';
import '../util/format.dart';
import '../util/label.dart';
import '../util/validasi.dart';

/// Registrasi Pasien Singkat (SKPL Tabel 7.1 no. 3, FR-02): identitas minimal lalu kunjungan berstatus menunggu.
/// Pasien lama dicari dulu supaya tidak terdaftar dua kali.
class HalamanRegistrasi extends ConsumerStatefulWidget {
  const HalamanRegistrasi({super.key});

  @override
  ConsumerState<HalamanRegistrasi> createState() => _HalamanRegistrasiState();
}

class _HalamanRegistrasiState extends ConsumerState<HalamanRegistrasi> {
  final _form = GlobalKey<FormState>();
  final _cari = TextEditingController();
  final _nama = TextEditingController();
  final _usia = TextEditingController();
  final _nik = TextEditingController();
  final _telepon = TextEditingController();
  JenisKelamin? _kelamin;
  DateTime? _tanggalLahir;
  bool _tahuTanggalLahir = true;

  List<PasienRingkas>? _hasilCari;
  bool _mencari = false;
  bool _sibuk = false;
  bool _dicoba = false;
  GalatApi? _galat;

  @override
  void dispose() {
    for (final pengendali in [_cari, _nama, _usia, _nik, _telepon]) {
      pengendali.dispose();
    }
    super.dispose();
  }

  Future<void> _jalankanCari() async {
    final kata = _cari.text.trim();
    if (kata.length < 2) {
      tampilkanPesan(context, 'Ketik minimal 2 huruf nama, atau NIK lengkap.');
      return;
    }
    setState(() => _mencari = true);
    try {
      final hasil = await ref.read(repositoriProvider).cariPasien(kata);
      if (mounted) setState(() => _hasilCari = hasil);
    } on GalatApi catch (galat) {
      if (mounted) tampilkanPesan(context, galat.field('q') ?? galat.pesan, galat: true);
    } finally {
      if (mounted) setState(() => _mencari = false);
    }
  }

  void _bukaForm(String idKunjungan, PasienTriase pasien, {DateTime? waktuDatang}) {
    context.push(
      Rute.formTriase(idKunjungan),
      extra: InfoFormTriase(pasien: pasien, waktuDatang: waktuDatang),
    );
  }

  PasienTriase _pasienDari(PasienRingkas p) =>
      PasienTriase(idPasien: p.idPasien, nama: p.nama, usia: p.usia, jenisKelamin: p.jenisKelamin);

  Future<void> _pilihPasienLama(PasienRingkas pasien) async {
    final aktif = pasien.idKunjunganAktif;
    if (aktif != null) {
      final buka = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Kunjungan masih aktif'),
          content: Text('${pasien.nama} masih punya kunjungan yang menunggu atau sedang ditangani.'),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Batal')),
            FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Isi triase kunjungan ini')),
          ],
        ),
      );
      if (buka == true && mounted) _bukaForm(aktif, _pasienDari(pasien));
      return;
    }
    await _daftarkan(
      RegistrasiRequest(
        idPasien: pasien.idPasien,
        nama: null,
        tanggalLahir: null,
        perkiraanUsia: null,
        jenisKelamin: null,
        nik: null,
        noTelepon: null,
      ),
      _pasienDari(pasien),
    );
  }

  Future<void> _daftarkanBaru() async {
    setState(() => _dicoba = true);
    final formValid = _form.currentState!.validate();
    final tanggalOk = !_tahuTanggalLahir || _tanggalLahir != null;
    if (!formValid || _kelamin == null || !tanggalOk) return;
    final usia = _tahuTanggalLahir ? null : int.parse(_usia.text.trim());
    final data = RegistrasiRequest(
      idPasien: null,
      nama: _nama.text.trim(),
      jenisKelamin: _kelamin,
      tanggalLahir: _tahuTanggalLahir ? _tanggalLahir : null,
      perkiraanUsia: usia,
      nik: _nik.text.trim().isEmpty ? null : _nik.text.trim(),
      noTelepon: _telepon.text.trim().isEmpty ? null : _telepon.text.trim(),
    );
    final hariIni = DateTime.now();
    final tanggal = _tanggalLahir;
    final usiaTampil =
        usia ??
        (tanggal == null
            ? null
            : hariIni.year -
                  tanggal.year -
                  (DateTime(hariIni.year, tanggal.month, tanggal.day).isAfter(hariIni) ? 1 : 0));
    await _daftarkan(data, PasienTriase(idPasien: '', nama: data.nama!, usia: usiaTampil, jenisKelamin: _kelamin!));
  }

  Future<void> _daftarkan(RegistrasiRequest data, PasienTriase pasien) async {
    setState(() {
      _sibuk = true;
      _galat = null;
    });
    try {
      final KunjunganDibuatResponse hasil = await ref.read(repositoriProvider).registrasi(data);
      if (!mounted) return;
      unawaited(ref.read(antreanProvider.notifier).muatUlang());
      _bersihkan();
      _bukaForm(
        hasil.idKunjungan,
        PasienTriase(idPasien: hasil.idPasien, nama: pasien.nama, usia: pasien.usia, jenisKelamin: pasien.jenisKelamin),
        waktuDatang: hasil.waktuDatang,
      );
    } on GalatApi catch (galat) {
      if (!mounted) return;
      setState(() => _galat = galat);
      final aktif = galat.ekstra['id_kunjungan_aktif'];
      if (aktif is String) {
        tampilkanPesan(context, galat.pesan, galat: true);
        _bukaForm(aktif, pasien);
      }
    } finally {
      if (mounted) setState(() => _sibuk = false);
    }
  }

  void _bersihkan() {
    _form.currentState?.reset();
    for (final pengendali in [_cari, _nama, _usia, _nik, _telepon]) {
      pengendali.clear();
    }
    setState(() {
      _kelamin = null;
      _tanggalLahir = null;
      _tahuTanggalLahir = true;
      _hasilCari = null;
      _dicoba = false;
    });
  }

  Future<void> _pilihTanggal() async {
    final hariIni = DateTime.now();
    final tanggal = await showDatePicker(
      context: context,
      initialDate: _tanggalLahir ?? DateTime(hariIni.year - 30),
      firstDate: DateTime(hariIni.year - 150),
      lastDate: hariIni,
      helpText: 'Tanggal lahir',
    );
    if (tanggal != null) setState(() => _tanggalLahir = tanggal);
  }

  @override
  Widget build(BuildContext context) {
    final galat = _galat;
    final hasilCari = _hasilCari;
    return Scaffold(
      appBar: AppBar(title: const Text('Triase Baru')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          KartuBagian(
            judul: 'Pasien lama',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                TextField(
                  key: const ValueKey('cari-pasien'),
                  controller: _cari,
                  textInputAction: TextInputAction.search,
                  onSubmitted: (_) => _jalankanCari(),
                  decoration: InputDecoration(
                    labelText: 'Cari nama atau NIK',
                    suffixIcon: _mencari
                        ? const Padding(padding: EdgeInsets.all(14), child: CircularProgressIndicator(strokeWidth: 2))
                        : IconButton(tooltip: 'Cari', icon: const Icon(Icons.search), onPressed: _jalankanCari),
                  ),
                ),
                if (hasilCari != null) ...[
                  const SizedBox(height: 8),
                  if (hasilCari.isEmpty)
                    const Text(
                      'Pasien tidak ditemukan. Daftarkan sebagai pasien baru di bawah.',
                      style: TextStyle(color: Warna.teksRedup),
                    )
                  else
                    for (final pasien in hasilCari)
                      ListTile(
                        contentPadding: EdgeInsets.zero,
                        title: Text(pasien.nama),
                        subtitle: Text(
                          [
                            if (pasien.usia != null) '${pasien.usia} th',
                            labelKelamin(pasien.jenisKelamin),
                            if (pasien.nikTersamar != null) 'NIK ${pasien.nikTersamar}',
                            if (pasien.idKunjunganAktif != null) 'kunjungan aktif',
                          ].join(' · '),
                        ),
                        trailing: const Icon(Icons.chevron_right),
                        enabled: !_sibuk,
                        onTap: () => _pilihPasienLama(pasien),
                      ),
                ],
              ],
            ),
          ),
          const SizedBox(height: 16),
          KartuBagian(
            judul: 'Pasien baru',
            child: Form(
              key: _form,
              autovalidateMode: _dicoba ? AutovalidateMode.onUserInteraction : AutovalidateMode.disabled,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  if (galat != null && galat.pesanField.isEmpty) ...[
                    KotakPesan(galat.pesan),
                    const SizedBox(height: 12),
                  ],
                  TextFormField(
                    key: const ValueKey('nama'),
                    controller: _nama,
                    textCapitalization: TextCapitalization.words,
                    decoration: InputDecoration(labelText: 'Nama', errorText: galat?.field('nama')),
                    validator: (teks) => periksaPanjang(teks ?? '', min: 1, maks: 120, nama: 'Nama'),
                  ),
                  const SizedBox(height: 16),
                  const Text('Jenis kelamin', style: TextStyle(fontWeight: FontWeight.w600)),
                  const SizedBox(height: 8),
                  SegmentedButton<JenisKelamin>(
                    segments: const [
                      ButtonSegment(value: JenisKelamin.lakiLaki, label: Text('Laki-laki')),
                      ButtonSegment(value: JenisKelamin.perempuan, label: Text('Perempuan')),
                    ],
                    selected: {?_kelamin},
                    emptySelectionAllowed: true,
                    showSelectedIcon: false,
                    onSelectionChanged: (pilihan) => setState(() => _kelamin = pilihan.firstOrNull),
                  ),
                  if ((_dicoba && _kelamin == null) || galat?.field('jenis_kelamin') != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 6),
                      child: Text(
                        galat?.field('jenis_kelamin') ?? 'Pilih jenis kelamin.',
                        style: const TextStyle(color: Warna.galat, fontSize: 12),
                      ),
                    ),
                  const SizedBox(height: 8),
                  SwitchListTile(
                    contentPadding: EdgeInsets.zero,
                    title: const Text('Tanggal lahir diketahui'),
                    value: _tahuTanggalLahir,
                    onChanged: (nilai) => setState(() => _tahuTanggalLahir = nilai),
                  ),
                  if (_tahuTanggalLahir)
                    InputDecorator(
                      decoration: InputDecoration(
                        labelText: 'Tanggal lahir',
                        errorText:
                            galat?.field('tanggal_lahir') ??
                            (_dicoba && _tanggalLahir == null ? 'Pilih tanggal lahir.' : null),
                      ),
                      child: InkWell(
                        onTap: _pilihTanggal,
                        child: Row(
                          children: [
                            Expanded(
                              child: Text(_tanggalLahir == null ? 'Pilih tanggal' : tanggalSaja(_tanggalLahir!)),
                            ),
                            const Icon(Icons.calendar_today_outlined, size: 20),
                          ],
                        ),
                      ),
                    )
                  else
                    TextFormField(
                      key: const ValueKey('perkiraan-usia'),
                      controller: _usia,
                      keyboardType: TextInputType.number,
                      inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                      decoration: InputDecoration(
                        labelText: 'Perkiraan usia (tahun)',
                        errorText: galat?.field('perkiraan_usia'),
                      ),
                      validator: (teks) => periksaUsia(teks ?? ''),
                    ),
                  const SizedBox(height: 16),
                  TextFormField(
                    key: const ValueKey('nik'),
                    controller: _nik,
                    keyboardType: TextInputType.number,
                    inputFormatters: [FilteringTextInputFormatter.digitsOnly, LengthLimitingTextInputFormatter(16)],
                    decoration: InputDecoration(labelText: 'NIK (opsional)', errorText: galat?.field('nik')),
                    validator: (teks) => periksaNik(teks ?? ''),
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    key: const ValueKey('telepon'),
                    controller: _telepon,
                    keyboardType: TextInputType.phone,
                    decoration: InputDecoration(
                      labelText: 'Nomor telepon (opsional)',
                      errorText: galat?.field('no_telepon'),
                    ),
                    validator: (teks) => periksaTelepon(teks ?? ''),
                  ),
                  const SizedBox(height: 20),
                  TombolProses(label: 'Daftarkan dan isi triase', sibuk: _sibuk, onPressed: _daftarkanBaru),
                ],
              ),
            ),
          ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }
}
