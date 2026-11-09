// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:json_annotation/json_annotation.dart';

/// 18 kategori keluhan, sama persis dengan kategori saat model Random Forest dilatih.
@JsonEnum()
enum KategoriKeluhan {
  @JsonValue('Penurunan kesadaran atau kejang')
  penurunanKesadaranAtauKejang('Penurunan kesadaran atau kejang'),
  @JsonValue('Nyeri dada')
  nyeriDada('Nyeri dada'),
  @JsonValue('Sesak napas atau batuk')
  sesakNapasAtauBatuk('Sesak napas atau batuk'),
  @JsonValue('Perdarahan')
  perdarahan('Perdarahan'),
  @JsonValue('Gangguan saraf')
  gangguanSaraf('Gangguan saraf'),
  @JsonValue('Nyeri perut')
  nyeriPerut('Nyeri perut'),
  @JsonValue('Demam')
  demam('Demam'),
  @JsonValue('Pusing')
  pusing('Pusing'),
  @JsonValue('Nyeri kepala')
  nyeriKepala('Nyeri kepala'),
  /// Incorrect name has been replaced. Original name: `Mual, muntah, atau diare`.
  @JsonValue('Mual, muntah, atau diare')
  undefined0('Mual, muntah, atau diare'),
  @JsonValue('Cedera atau luka')
  cederaAtauLuka('Cedera atau luka'),
  @JsonValue('Jantung berdebar')
  jantungBerdebar('Jantung berdebar'),
  @JsonValue('Kulit atau alergi')
  kulitAtauAlergi('Kulit atau alergi'),
  /// Incorrect name has been replaced. Original name: `Mata, telinga, hidung, atau tenggorokan`.
  @JsonValue('Mata, telinga, hidung, atau tenggorokan')
  undefined1('Mata, telinga, hidung, atau tenggorokan'),
  /// Incorrect name has been replaced. Original name: `Nyeri punggung, pinggang, atau anggota gerak`.
  @JsonValue('Nyeri punggung, pinggang, atau anggota gerak')
  undefined2('Nyeri punggung, pinggang, atau anggota gerak'),
  @JsonValue('Lemas atau kelemahan umum')
  lemasAtauKelemahanUmum('Lemas atau kelemahan umum'),
  @JsonValue('Keluhan kemih atau kandungan')
  keluhanKemihAtauKandungan('Keluhan kemih atau kandungan'),
  @JsonValue('Lainnya')
  lainnya('Lainnya'),
  /// Default value for all unparsed values, allows backward compatibility when adding new values on the backend.
  $unknown(null);

  const KategoriKeluhan(this.json);

  factory KategoriKeluhan.fromJson(String json) => values.firstWhere(
        (e) => e.json == json,
        orElse: () => $unknown,
      );

  final String? json;

  @override
  String toString() => json?.toString() ?? super.toString();
  /// Returns all defined enum values excluding the $unknown value.
  static List<KategoriKeluhan> get $valuesDefined => values.where((value) => value != $unknown).toList();
}
