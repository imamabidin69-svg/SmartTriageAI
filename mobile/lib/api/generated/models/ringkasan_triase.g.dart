// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'ringkasan_triase.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

RingkasanTriase _$RingkasanTriaseFromJson(Map<String, dynamic> json) =>
    RingkasanTriase(
      keluhanUtama: json['keluhan_utama'] as String,
      gejala: json['gejala'] as String,
      onset: json['onset'] as String,
      kategoriKeluhan: KategoriKeluhan.fromJson(
        json['kategori_keluhan'] as String,
      ),
    );

Map<String, dynamic> _$RingkasanTriaseToJson(RingkasanTriase instance) =>
    <String, dynamic>{
      'keluhan_utama': instance.keluhanUtama,
      'gejala': instance.gejala,
      'onset': instance.onset,
      'kategori_keluhan': _$KategoriKeluhanEnumMap[instance.kategoriKeluhan]!,
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
