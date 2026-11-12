import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/galat_api.dart';
import '../komponen/umum.dart';
import '../state/sesi.dart';
import '../tema.dart';

/// Logo SmartTriage AI (kotak putih berisi perisai), dipakai di halaman masuk dan saat memeriksa sesi.
class LogoAplikasi extends StatelessWidget {
  const LogoAplikasi({super.key, this.ukuran = 52});

  final double ukuran;

  @override
  Widget build(BuildContext context) {
    return Image.asset(
      'assets/logo/logo.png',
      width: ukuran,
      height: ukuran,
      filterQuality: FilterQuality.medium,
      excludeFromSemantics: true,
    );
  }
}

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
      backgroundColor: Colors.white,
      body: SafeArea(
        // SliverFillRemaining membuat catatan kerahasiaan menempel di bawah layar, tapi tetap bisa digulir
        // bila papan ketik terbuka atau ukuran huruf diperbesar.
        child: CustomScrollView(
          slivers: [
            SliverFillRemaining(
              hasScrollBody: false,
              child: Align(
                alignment: Alignment.topCenter,
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 440),
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(24, 28, 24, 20),
                    child: Form(
                      key: _form,
                      child: AutofillGroup(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            const Row(
                              children: [
                                LogoAplikasi(),
                                SizedBox(width: 12),
                                Flexible(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        'SmartTriage AI',
                                        style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
                                      ),
                                      Text('Instalasi Gawat Darurat', style: TextStyle(color: Warna.teksRedup)),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 40),
                            Semantics(
                              header: true,
                              child: const Text('Masuk', style: TextStyle(fontSize: 30, fontWeight: FontWeight.w700)),
                            ),
                            const SizedBox(height: 6),
                            const Text(
                              'Untuk perawat dan dokter ICU.',
                              style: TextStyle(color: Warna.teksRedup, fontSize: 16),
                            ),
                            const SizedBox(height: 24),
                            if (galat != null) ...[
                              KotakPesan(
                                galat.status == 401 ? 'Periksa kembali email dan password Anda.' : galat.pesan,
                              ),
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
                            const SizedBox(height: 18),
                            TextFormField(
                              controller: _password,
                              decoration: InputDecoration(
                                labelText: 'Password',
                                errorText: galat?.field('password'),
                                suffixIcon: IconButton(
                                  tooltip: _tampilkanPassword ? 'Sembunyikan password' : 'Tampilkan password',
                                  icon: Icon(
                                    _tampilkanPassword ? Icons.visibility_off_outlined : Icons.visibility_outlined,
                                  ),
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
                            const SizedBox(height: 14),
                            const Text(
                              'Lupa password? Minta admin ICU untuk mengatur ulang.',
                              style: TextStyle(color: Warna.teksRedup, fontSize: 14),
                            ),
                            const Spacer(),
                            const SizedBox(height: 32),
                            const Divider(color: Warna.garisLembut),
                            const SizedBox(height: 14),
                            const Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Icon(Icons.lock_outline, size: 18, color: Warna.teksSamar),
                                SizedBox(width: 8),
                                Expanded(
                                  child: Text(
                                    'Data pasien bersifat rahasia. Jangan bagikan akun Anda kepada siapa pun.',
                                    style: TextStyle(color: Warna.teksSamar, fontSize: 13, height: 1.4),
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ],
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
      backgroundColor: Colors.white,
      body: SafeArea(
        child: sesi.hasError
            ? TampilanGalat(sesi.error!, cobaLagi: ref.read(sesiProvider.notifier).cobaLagi)
            : const Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    LogoAplikasi(ukuran: 72),
                    SizedBox(height: 28),
                    TampilanMemuat(pesan: 'Memeriksa sesi...'),
                  ],
                ),
              ),
      ),
    );
  }
}
