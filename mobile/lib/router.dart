import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'api/generated/models/pasien_triase.dart';
import 'api/generated/models/peran.dart';
import 'halaman/daftar_tunggu.dart';
import 'halaman/eir.dart';
import 'halaman/form_triase.dart';
import 'halaman/hasil.dart';
import 'halaman/kerangka.dart';
import 'halaman/login.dart';
import 'halaman/pemindaian.dart';
import 'halaman/profil.dart';
import 'halaman/registrasi.dart';
import 'halaman/riwayat.dart';
import 'rute.dart';
import 'state/sesi.dart';

/// Ke mana pengguna diarahkan berdasarkan status login. Dipisah supaya mudah diuji.
String? arahkan(AsyncValue<Object?> sesi, Peran? peran, String lokasi) {
  if (!sesi.hasValue) return lokasi == Rute.mulai ? null : Rute.mulai;
  final masuk = sesi.value != null;
  if (!masuk) return lokasi == Rute.masuk ? null : Rute.masuk;
  if (lokasi == Rute.masuk || lokasi == Rute.mulai) return Rute.antrean;
  // Registrasi dan input triase hanya untuk perawat; server juga menolaknya.
  if (peran != Peran.perawat && lokasi == Rute.triaseBaru) return Rute.antrean;
  return null;
}

final routerProvider = Provider<GoRouter>((ref) {
  final penanda = ValueNotifier<int>(0);
  ref.listen(sesiProvider, (_, _) => penanda.value++);
  final router = GoRouter(
    initialLocation: Rute.antrean,
    refreshListenable: penanda,
    redirect: (context, state) => arahkan(ref.read(sesiProvider), ref.read(peranProvider), state.matchedLocation),
    routes: [
      GoRoute(path: Rute.mulai, builder: (_, _) => const HalamanMulai()),
      GoRoute(path: Rute.masuk, builder: (_, _) => const HalamanLogin()),
      StatefulShellRoute.indexedStack(
        builder: (_, _, navigasi) => KerangkaUtama(navigasi: navigasi),
        branches: [
          StatefulShellBranch(
            routes: [GoRoute(path: Rute.antrean, builder: (_, _) => const HalamanDaftarTunggu())],
          ),
          StatefulShellBranch(
            routes: [GoRoute(path: Rute.triaseBaru, builder: (_, _) => const HalamanRegistrasi())],
          ),
          StatefulShellBranch(
            routes: [GoRoute(path: Rute.riwayat, builder: (_, _) => const HalamanCariRiwayat())],
          ),
          StatefulShellBranch(
            routes: [GoRoute(path: Rute.profil, builder: (_, _) => const HalamanProfil())],
          ),
        ],
      ),
      GoRoute(
        path: '/triase/:idTriase',
        builder: (_, state) =>
            HalamanHasil(idTriase: state.pathParameters['idTriase']!, info: state.extra as InfoHasil?),
      ),
      GoRoute(
        path: '/kunjungan/:idKunjungan/triase',
        builder: (_, state) =>
            HalamanFormTriase(idKunjungan: state.pathParameters['idKunjungan']!, info: state.extra as InfoFormTriase?),
      ),
      GoRoute(
        path: '/kunjungan/:idKunjungan/kode-eir',
        builder: (_, state) =>
            HalamanKodeQrEir(idKunjungan: state.pathParameters['idKunjungan']!, pasien: state.extra as PasienTriase?),
      ),
      GoRoute(
        path: '/kunjungan/:idKunjungan/ringkasan-eir',
        builder: (_, state) =>
            HalamanRingkasanEir(idKunjungan: state.pathParameters['idKunjungan']!, namaPasien: state.extra as String?),
      ),
      GoRoute(
        path: '/pasien/:idPasien/riwayat',
        builder: (_, state) =>
            HalamanRiwayatPasien(idPasien: state.pathParameters['idPasien']!, pasien: state.extra as PasienTriase?),
      ),
      GoRoute(path: Rute.pemindaian, builder: (_, _) => const HalamanPemindaian()),
    ],
  );
  ref.onDispose(() {
    router.dispose();
    penanda.dispose();
  });
  return router;
});
