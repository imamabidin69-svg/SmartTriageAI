// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'triase_input.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

TriaseInput _$TriaseInputFromJson(Map<String, dynamic> json) => TriaseInput(
  keluhanUtama: json['keluhan_utama'] as String,
  gejala: json['gejala'] as String,
  kategoriKeluhan: KategoriKeluhan.fromJson(json['kategori_keluhan'] as String),
  skalaNyeri: (json['skala_nyeri'] as num).toInt(),
  tingkatKesadaran: TingkatKesadaran.fromJson(
    json['tingkat_kesadaran'] as String,
  ),
  tandaVital: TandaVital.fromJson(json['tanda_vital'] as Map<String, dynamic>),
  idPemindaian: (json['id_pemindaian'] as List<dynamic>?)
      ?.map((e) => e as String)
      .toList(),
);

Map<String, dynamic> _$TriaseInputToJson(
  TriaseInput instance,
) => <String, dynamic>{
  'keluhan_utama': instance.keluhanUtama,
  'gejala': instance.gejala,
  'kategori_keluhan': _$KategoriKeluhanEnumMap[instance.kategoriKeluhan]!,
  'skala_nyeri': instance.skalaNyeri,
  'tingkat_kesadaran': _$TingkatKesadaranEnumMap[instance.tingkatKesadaran]!,
  'tanda_vital': instance.tandaVital,
  'id_pemindaian': instance.idPemindaian,
};

const _$KategoriKeluhanEnumMap = {
  KategoriKeluhan.penurunanKesadaranAtauKejang:
      'Penurunan kesadaran atau kejang',
  KategoriKeluhan.nyeriDada: 'Nyeri dada',
  KategoriKeluhan.sesakNapasAtauBatuk: 'Sesak napas atau batuk',
  KategoriKeluhan.perdarahan: 'Perdarahan',
  KategoriKeluhan.gangguanSaraf: 'Gangguan saraf',
  KategoriKeluhan.nyeriPerut: 'Nyeri perut',
  KategoriKeluhan.demam: 'Demam',
  KategoriKeluhan.pusing: 'Pusing',
  KategoriKeluhan.nyeriKepala: 'Nyeri kepala',
  KategoriKeluhan.undefined0: 'Mual, muntah, atau diare',
  KategoriKeluhan.cederaAtauLuka: 'Cedera atau luka',
  KategoriKeluhan.jantungBerdebar: 'Jantung berdebar',
  KategoriKeluhan.kulitAtauAlergi: 'Kulit atau alergi',
  KategoriKeluhan.undefined1: 'Mata, telinga, hidung, atau tenggorokan',
  KategoriKeluhan.undefined2: 'Nyeri punggung, pinggang, atau anggota gerak',
  KategoriKeluhan.lemasAtauKelemahanUmum: 'Lemas atau kelemahan umum',
  KategoriKeluhan.keluhanKemihAtauKandungan: 'Keluhan kemih atau kandungan',
  KategoriKeluhan.lainnya: 'Lainnya',
  KategoriKeluhan.$unknown: r'$unknown',
};

const _$TingkatKesadaranEnumMap = {
  TingkatKesadaran.a: 'A',
  TingkatKesadaran.v: 'V',
  TingkatKesadaran.p: 'P',
  TingkatKesadaran.u: 'U',
  TingkatKesadaran.$unknown: r'$unknown',
};
