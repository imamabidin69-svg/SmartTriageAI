// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

@JsonEnum()
enum ItemPeringatanJenis {
  @JsonValue('kritis_belum_divalidasi')
  kritisBelumDivalidasi('kritis_belum_divalidasi'),
  @JsonValue('level_naik')
  levelNaik('level_naik'),
  @JsonValue('tanda_bahaya_eir')
  tandaBahayaEir('tanda_bahaya_eir'),
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
