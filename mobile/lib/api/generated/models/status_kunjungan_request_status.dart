// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

/// ditangani saat pasien mulai menjalani tindakan atau operasi, menunggu saat kembali dipantau setelah tindakan, selesai saat pasien keluar ICU (pindah ruangan, pulang, atau meninggal).
@JsonEnum()
enum StatusKunjunganRequestStatus {
  @JsonValue('menunggu')
  menunggu('menunggu'),
  @JsonValue('ditangani')
  ditangani('ditangani'),
  @JsonValue('selesai')
  selesai('selesai'),
  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const StatusKunjunganRequestStatus(this.json);

  factory StatusKunjunganRequestStatus.fromJson(String json) => values.firstWhere(
        (e) => e.json == json,
        orElse: () => $unknown,
      );

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();
  /// Returns all defined enum values excluding the $unknown value.
  static List<StatusKunjunganRequestStatus> get $valuesDefined => values.where((value) => value != $unknown).toList();
}
