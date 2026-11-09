import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'router.dart';
import 'tema.dart';

void main() {
  // Percobaan ulang otomatis Riverpod dimatikan: error ditampilkan dengan tombol Coba lagi, dan daftar tunggu
  // sudah dimuat ulang sendiri setiap 15 detik.
  runApp(ProviderScope(retry: (_, _) => null, child: const AplikasiSmartTriage()));
}

class AplikasiSmartTriage extends ConsumerWidget {
  const AplikasiSmartTriage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return MaterialApp.router(
      title: 'SmartTriage AI',
      debugShowCheckedModeBanner: false,
      theme: temaAplikasi(),
      routerConfig: ref.watch(routerProvider),
      locale: const Locale('id', 'ID'),
      supportedLocales: const [Locale('id', 'ID')],
      localizationsDelegates: GlobalMaterialLocalizations.delegates,
    );
  }
}
