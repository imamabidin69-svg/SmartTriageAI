// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

@JsonEnum()
enum ItemPeringatanJenis {
  @JsonValue('menunggu_persetujuan')
  menungguPersetujuan('menunggu_persetujuan'),
  @JsonValue('observasi_terlambat')
  observasiTerlambat('observasi_terlambat'),
  @JsonValue('informasi_penting_eir')
  informasiPentingEir('informasi_penting_eir'),
  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const ItemPeringatanJenis(this.json);

  factory ItemPeringatanJenis.fromJson(String json) => values.firstWhere(
        (e) => e.json == json,
        orElse: () => $unknown,
      );

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();
  /// Returns all defined enum values excluding the $unknown value.
  static List<ItemPeringatanJenis> get $valuesDefined => values.where((value) => value != $unknown).toList();
}
