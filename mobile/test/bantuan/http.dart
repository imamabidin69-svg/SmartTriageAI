import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';

/// Adapter HTTP tiruan untuk dio: mencatat setiap request lalu menjawab sesuai fungsi [jawab].
class AdapterPalsu implements HttpClientAdapter {
  AdapterPalsu(this.jawab);

  final Future<ResponseBody> Function(RequestOptions opsi) jawab;
  final List<RequestOptions> permintaan = [];

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    // Isi body ikut dibaca supaya FormData benar-benar dikirim, sama seperti adapter asli.
    if (requestStream != null) await requestStream.drain<void>();
    permintaan.add(options);
    return jawab(options);
  }

  @override
  void close({bool force = false}) {}
}

ResponseBody jawabanJson(int status, Object? isi) => ResponseBody.fromString(
  isi == null ? '' : jsonEncode(isi),
  status,
  headers: {
    Headers.contentTypeHeader: [Headers.jsonContentType],
  },
);

Map<String, Object?> problem(int status, String tipe, {String judul = 'Galat', String? detail}) => {
  'type': tipe,
  'title': judul,
  'status': status,
  'detail': ?detail,
};
