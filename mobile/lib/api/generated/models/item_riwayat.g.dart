// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'item_riwayat.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ItemRiwayat _$ItemRiwayatFromJson(Map<String, dynamic> json) => ItemRiwayat(
  idTriase: json['id_triase'] as String,
  jenis: JenisTriase.fromJson(json['jenis'] as String),
  waktuTriase: DateTime.parse(json['waktu_triase'] as String),
  keluhanUtama: json['keluhan_utama'] as String,
  kategoriKeluhan: json['kategori_keluhan'] == null
      ? null
      : KategoriKeluhan.fromJson(json['kategori_keluhan'] as String),
  riskLevel: RiskLevel.fromJson(json['risk_level'] as String),
  sumberRekomendasi: SumberRekomendasi.fromJson(
    json['sumber_rekomendasi'] as String,
  ),
  statusValidasi: StatusValidasi.fromJson(json['status_validasi'] as String),
  tandaVital: TandaVitalResponse.fromJson(
    json['tanda_vital'] as Map<String, dynamic>,
  ),
  dibuatOleh: PenggunaRingkas.fromJson(
    json['dibuat_oleh'] as Map<String, dynamic>,
  ),
  divalidasiOleh: json['divalidasi_oleh'] == null
      ? null
      : PenggunaRingkas.fromJson(
          json['divalidasi_oleh'] as Map<String, dynamic>,
        ),
  kunjungan: KunjunganRiwayat.fromJson(
    json['kunjungan'] as Map<String, dynamic>,
  ),
);

Map<String, dynamic> _$ItemRiwayatToJson(
  ItemRiwayat instance,
) => <String, dynamic>{
  'id_triase': instance.idTriase,
  'jenis': _$JenisTriaseEnumMap[instance.jenis]!,
  'waktu_triase': instance.waktuTriase.toIso8601String(),
  'keluhan_utama': instance.keluhanUtama,
  'kategori_keluhan': _$KategoriKeluhanEnumMap[instance.kategoriKeluhan],
  'risk_level': _$RiskLevelEnumMap[instance.riskLevel]!,
  'sumber_rekomendasi': _$SumberRekomendasiEnumMap[instance.sumberRekomendasi]!,
  'status_validasi': _$StatusValidasiEnumMap[instance.statusValidasi]!,
  'tanda_vital': instance.tandaVital,
  'dibuat_oleh': instance.dibuatOleh,
  'divalidasi_oleh': instance.divalidasiOleh,
  'kunjungan': instance.kunjungan,
};

const _$JenisTriaseEnumMap = {
  JenisTriase.awal: 'awal',
  JenisTriase.ulang: 'ulang',
  JenisTriase.$unknown: r'$unknown',
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

const _$RiskLevelEnumMap = {
  RiskLevel.rendah: 'rendah',
  RiskLevel.sedang: 'sedang',
  RiskLevel.tinggi: 'tinggi',
  RiskLevel.kritis: 'kritis',
  RiskLevel.$unknown: r'$unknown',
};

const _$SumberRekomendasiEnumMap = {
  SumberRekomendasi.model: 'model',
  SumberRekomendasi.aturan: 'aturan',
  SumberRekomendasi.$unknown: r'$unknown',
};

const _$StatusValidasiEnumMap = {
  StatusValidasi.menunggu: 'menunggu',
  StatusValidasi.disetujui: 'disetujui',
  StatusValidasi.menungguReviewDokter: 'menunggu_review_dokter',
  StatusValidasi.dikoreksi: 'dikoreksi',
  StatusValidasi.$unknown: r'$unknown',
};
