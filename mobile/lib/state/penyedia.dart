import 'dart:io';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';

import '../api/klien_http.dart';
import '../api/penyimpanan_token.dart';
import '../api/repositori.dart';
import '../konfigurasi.dart';
import 'sesi.dart';

final penyimpananTokenProvider = Provider<PenyimpananToken>((ref) => PenyimpananTokenAman());

final klienHttpProvider = Provider<KlienHttp>(
  (ref) => KlienHttp(
    alamat: alamatApi,
    token: ref.watch(penyimpananTokenProvider),
    saatSesiBerakhir: () => ref.read(sesiProvider.notifier).berakhir(),
  ),
);

final repositoriProvider = Provider<RepositoriApi>((ref) => RepositoriApi(ref.watch(klienHttpProvider)));

/// Membuka kamera bawaan perangkat (keputusan M6). Foto disimpan sementara di cache aplikasi, bukan di galeri,
/// lalu dihapus setelah dikirim. Diganti di tes.
typedef PengambilFoto = Future<File?> Function();

final pengambilFotoProvider = Provider<PengambilFoto>(
  (ref) => () async {
    final foto = await ImagePicker().pickImage(
      source: ImageSource.camera,
      preferredCameraDevice: CameraDevice.rear,
      // Model membaca foto 640 piksel, jadi foto besar cukup diperkecil di perangkat supaya cepat terkirim.
      maxWidth: 1600,
      imageQuality: 85,
    );
    return foto == null ? null : File(foto.path);
  },
);
