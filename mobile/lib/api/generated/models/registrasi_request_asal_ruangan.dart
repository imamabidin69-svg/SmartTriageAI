// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

@JsonEnum()
enum RegistrasiRequestAsalRuangan {
  @JsonValue('IGD')
  igd('IGD'),
  @JsonValue('Kamar operasi')
  kamarOperasi('Kamar operasi'),
  @JsonValue('Rawat inap')
  rawatInap('Rawat inap'),
  @JsonValue('Rujukan rumah sakit lain')
  rujukanRumahSakitLain('Rujukan rumah sakit lain'),
  @JsonValue('Lainnya')
  lainnya('Lainnya'),
  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const RegistrasiRequestAsalRuangan(this.json);

  factory RegistrasiRequestAsalRuangan.fromJson(String json) => values.firstWhere(
        (e) => e.json == json,
        orElse: () => $unknown,
      );

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();
  /// Returns all defined enum values excluding the $unknown value.
  static List<RegistrasiRequestAsalRuangan> get $valuesDefined => values.where((value) => value != $unknown).toList();
}
