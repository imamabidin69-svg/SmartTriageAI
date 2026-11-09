// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

/// Untuk sumber model: naik berarti faktor ini mendukung level yang direkomendasikan, turun berarti melawannya. Untuk sumber aturan: naik berarti menambah poin risiko; netral bila tidak ada aturan yang terpicu.
@JsonEnum()
enum FaktorResponseArah {
  @JsonValue('naik')
  naik('naik'),
  @JsonValue('turun')
  turun('turun'),
  @JsonValue('netral')
  netral('netral'),
  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const FaktorResponseArah(this.json);

  factory FaktorResponseArah.fromJson(String json) => values.firstWhere(
        (e) => e.json == json,
        orElse: () => $unknown,
      );

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();
  /// Returns all defined enum values excluding the $unknown value.
  static List<FaktorResponseArah> get $valuesDefined => values.where((value) => value != $unknown).toList();
}
