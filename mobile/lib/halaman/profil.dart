import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/galat_api.dart';
import '../komponen/umum.dart';
import '../konfigurasi.dart';
import '../state/penyedia.dart';
import '../state/sesi.dart';
import '../tema.dart';
import '../util/label.dart';

/// Profil (keputusan M5): data akun, ganti password, dan keluar.
class HalamanProfil extends ConsumerWidget {
  const HalamanProfil({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pengguna = ref.watch(penggunaProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Profil')),
      body: pengguna == null
          ? const SizedBox.shrink()
          : ListView(
              padding: const EdgeInsets.only(bottom: 24),
              children: [
                DecoratedBox(
                  decoration: const BoxDecoration(
                    color: Colors.white,
                    border: Border(bottom: BorderSide(color: Warna.garis)),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(16, 14, 16, 16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(pengguna.nama, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700)),
                        const SizedBox(height: 2),
                        Text(pengguna.email, style: const TextStyle(color: Warna.teksRedup)),
                        const SizedBox(height: 10),
                        Tanda(labelPeran(pengguna.peran), warna: Warna.kepala, ikon: Icons.badge_outlined),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                const KartuBagian(judul: 'Ganti password', child: FormGantiPassword()),
                const SizedBox(height: 20),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: OutlinedButton.icon(
                    style: OutlinedButton.styleFrom(
                      foregroundColor: Warna.galat,
                      side: const BorderSide(color: Color(0xFFD9867F)),
                    ),
                    onPressed: () => _keluar(context, ref),
                    icon: const Icon(Icons.logout),
                    label: const Text('Keluar'),
                  ),
                ),
                const SizedBox(height: 24),
                const Text(
                  'Server: $alamatApi',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: Warna.teksSamar, fontSize: 12),
                ),
              ],
            ),
    );
  }

  Future<void> _keluar(BuildContext context, WidgetRef ref) async {
    final yakin = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Keluar dari aplikasi?'),
        content: const Text('Anda perlu memasukkan email dan password lagi untuk masuk.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Batal')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Keluar')),
        ],
      ),
    );
    if (yakin == true) await ref.read(sesiProvider.notifier).keluar();
  }
}

class FormGantiPassword extends ConsumerStatefulWidget {
  const FormGantiPassword({super.key});

  @override
  ConsumerState<FormGantiPassword> createState() => _FormGantiPasswordState();
}

class _FormGantiPasswordState extends ConsumerState<FormGantiPassword> {
  final _form = GlobalKey<FormState>();
  final _lama = TextEditingController();
  final _baru = TextEditingController();
  final _ulang = TextEditingController();
  bool _sibuk = false;
  GalatApi? _galat;

  @override
  void dispose() {
    _lama.dispose();
    _baru.dispose();
    _ulang.dispose();
    super.dispose();
  }

  Future<void> _simpan() async {
    if (!_form.currentState!.validate()) return;
    setState(() {
      _sibuk = true;
      _galat = null;
    });
    try {
      await ref.read(repositoriProvider).gantiPassword(lama: _lama.text, baru: _baru.text);
      if (!mounted) return;
      _form.currentState!.reset();
      _lama.clear();
      _baru.clear();
      _ulang.clear();
      tampilkanPesan(context, 'Password berhasil diganti.');
    } on GalatApi catch (galat) {
      if (mounted) setState(() => _galat = galat);
    } finally {
      if (mounted) setState(() => _sibuk = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final galat = _galat;
    final adaPesanField = galat != null && galat.pesanField.isNotEmpty;
    return Form(
      key: _form,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (galat != null && !adaPesanField) ...[KotakPesan(galat.pesan), const SizedBox(height: 12)],
          TextFormField(
            controller: _lama,
            obscureText: true,
            decoration: InputDecoration(labelText: 'Password lama', errorText: galat?.field('password_lama')),
            validator: (nilai) => (nilai ?? '').isEmpty ? 'Password lama wajib diisi.' : null,
          ),
          const SizedBox(height: 18),
          TextFormField(
            controller: _baru,
            obscureText: true,
            decoration: InputDecoration(
              labelText: 'Password baru',
              helperText: '8 sampai 128 karakter',
              errorText: galat?.field('password_baru'),
            ),
            validator: (nilai) {
              final isi = nilai ?? '';
              if (isi.length < 8 || isi.length > 128) return 'Password baru harus 8 sampai 128 karakter.';
              if (isi == _lama.text) return 'Password baru harus berbeda dari password lama.';
              return null;
            },
          ),
          const SizedBox(height: 18),
          TextFormField(
            controller: _ulang,
            obscureText: true,
            decoration: const InputDecoration(labelText: 'Ulangi password baru'),
            validator: (nilai) => nilai != _baru.text ? 'Ulangan password tidak sama.' : null,
          ),
          const SizedBox(height: 20),
          TombolProses(label: 'Simpan password', sibuk: _sibuk, onPressed: _simpan),
        ],
      ),
    );
  }
}
