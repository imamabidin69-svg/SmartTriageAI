import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/galat_api.dart';
import '../komponen/umum.dart';
import '../state/sesi.dart';
import '../tema.dart';

/// Halaman Login (SKPL Tabel 7.1 no. 1). Login gagal lima kali dalam 15 menit dibatasi server (FR-01).
class HalamanLogin extends ConsumerStatefulWidget {
  const HalamanLogin({super.key});

  @override
  ConsumerState<HalamanLogin> createState() => _HalamanLoginState();
}

class _HalamanLoginState extends ConsumerState<HalamanLogin> {
  final _form = GlobalKey<FormState>();
  final _email = TextEditingController();
  final _password = TextEditingController();
  bool _sibuk = false;
  bool _tampilkanPassword = false;
  GalatApi? _galat;

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _masuk() async {
    if (!_form.currentState!.validate()) return;
    setState(() {
      _sibuk = true;
      _galat = null;
    });
    try {
      await ref.read(sesiProvider.notifier).masuk(_email.text.trim(), _password.text);
    } on GalatApi catch (galat) {
      if (mounted) setState(() => _galat = galat);
    } finally {
      if (mounted) setState(() => _sibuk = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final galat = _galat;
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: Form(
                key: _form,
                child: AutofillGroup(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Container(
                            width: 32,
                            height: 32,
                            decoration: BoxDecoration(color: Warna.utama, borderRadius: BorderRadius.circular(8)),
                          ),
                          const SizedBox(width: 12),
                          const Flexible(
                            child: Text('SmartTriage AI', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w700)),
                          ),
                        ],
                      ),
                      const SizedBox(height: 32),
                      const Text('Masuk', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w700)),
                      const SizedBox(height: 4),
                      const Text('Untuk perawat dan dokter IGD.', style: TextStyle(color: Warna.teksRedup)),
                      const SizedBox(height: 20),
                      if (galat != null) ...[
                        KotakPesan(galat.status == 401 ? 'Periksa kembali email dan password Anda.' : galat.pesan),
                        const SizedBox(height: 16),
                      ],
                      TextFormField(
                        controller: _email,
                        decoration: InputDecoration(labelText: 'Email', errorText: galat?.field('email')),
                        keyboardType: TextInputType.emailAddress,
                        autofillHints: const [AutofillHints.email],
                        textInputAction: TextInputAction.next,
                        validator: (nilai) {
                          final isi = nilai?.trim() ?? '';
                          if (isi.isEmpty) return 'Email wajib diisi.';
                          if (!isi.contains('@')) return 'Format email tidak valid.';
                          return null;
                        },
                      ),
                      const SizedBox(height: 16),
                      TextFormField(
                        controller: _password,
                        decoration: InputDecoration(
                          labelText: 'Password',
                          errorText: galat?.field('password'),
                          suffixIcon: IconButton(
                            tooltip: _tampilkanPassword ? 'Sembunyikan password' : 'Tampilkan password',
                            icon: Icon(_tampilkanPassword ? Icons.visibility_off : Icons.visibility),
                            onPressed: () => setState(() => _tampilkanPassword = !_tampilkanPassword),
                          ),
                        ),
                        obscureText: !_tampilkanPassword,
                        autofillHints: const [AutofillHints.password],
                        onFieldSubmitted: (_) => _masuk(),
                        validator: (nilai) => (nilai ?? '').isEmpty ? 'Password wajib diisi.' : null,
                      ),
                      const SizedBox(height: 24),
                      TombolProses(label: 'Masuk', sibuk: _sibuk, onPressed: _masuk),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Ditampilkan saat aplikasi memeriksa token tersimpan, atau bila server tidak bisa dihubungi saat itu.
class HalamanMulai extends ConsumerWidget {
  const HalamanMulai({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final sesi = ref.watch(sesiProvider);
    return Scaffold(
      body: SafeArea(
        child: sesi.hasError
            ? TampilanGalat(sesi.error!, cobaLagi: ref.read(sesiProvider.notifier).cobaLagi)
            : const TampilanMemuat(pesan: 'Memeriksa sesi...'),
      ),
    );
  }
}
