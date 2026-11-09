// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

/// Jenis klien. Tanpa header ini klien dianggap web dan token disimpan di cookie HttpOnly.
@JsonEnum()
enum XClient {
  @JsonValue('web')
  web('web'),
  @JsonValue('mobile')
  mobile('mobile'),
  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const XClient(this.json);

  factory XClient.fromJson(String json) => values.firstWhere(
        (e) => e.json == json,
        orElse: () => $unknown,
      );

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();
  /// Returns all defined enum values excluding the $unknown value.
  static List<XClient> get $valuesDefined => values.where((value) => value != $unknown).toList();
}
