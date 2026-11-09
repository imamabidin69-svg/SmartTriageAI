// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'triase_detail.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

TriaseDetail _$TriaseDetailFromJson(Map<String, dynamic> json) => TriaseDetail(
  idTriase: json['id_triase'] as String,
  idKunjungan: json['id_kunjungan'] as String,
  jenis: JenisTriase.fromJson(json['jenis'] as String),
  pasien: PasienTriase.fromJson(json['pasien'] as Map<String, dynamic>),
  keluhanUtama: json['keluhan_utama'] as String,
  gejala: json['gejala'] as String,
  kategoriKeluhan: json['kategori_keluhan'] == null
      ? null
      : KategoriKeluhan.fromJson(json['kategori_keluhan'] as String),
  skalaNyeri: (json['skala_nyeri'] as num?)?.toInt(),
  tingkatKesadaran: TingkatKesadaran.fromJson(
    json['tingkat_kesadaran'] as String,
  ),
  tandaVital: TandaVitalResponse.fromJson(
    json['tanda_vital'] as Map<String, dynamic>,
  ),
  sumberTandaVital: SumberTandaVital.fromJson(
    json['sumber_tanda_vital'] as String,
  ),
  riskLevel: RiskLevel.fromJson(json['risk_level'] as String),
  sumberRekomendasi: SumberRekomendasi.fromJson(
    json['sumber_rekomendasi'] as String,
  ),
  penjelasanAi: PenjelasanResponse.fromJson(
    json['penjelasan_ai'] as Map<String, dynamic>,
  ),
  statusValidasi: StatusValidasi.fromJson(json['status_validasi'] as String),
  dibuatOleh: PenggunaRingkas.fromJson(
    json['dibuat_oleh'] as Map<String, dynamic>,
  ),
  divalidasiOleh: json['divalidasi_oleh'] == null
      ? null
      : PenggunaRingkas.fromJson(
          json['divalidasi_oleh'] as Map<String, dynamic>,
        ),
  waktuTriase: DateTime.parse(json['waktu_triase'] as String),
  peringatan: (json['peringatan'] as List<dynamic>)
      .map((e) => Peringatan.fromJson(e as Map<String, dynamic>))
      .toList(),
  catatanValidasiTerakhir: json['catatan_validasi_terakhir'] as String?,
);

Map<String, dynamic> _$TriaseDetailToJson(
  TriaseDetail instance,
) => <String, dynamic>{
  'id_triase': instance.idTriase,
  'id_kunjungan': instance.idKunjungan,
  'jenis': _$JenisTriaseEnumMap[instance.jenis]!,
  'pasien': instance.pasien,
  'keluhan_utama': instance.keluhanUtama,
  'gejala': instance.gejala,
  'kategori_keluhan': _$KategoriKeluhanEnumMap[instance.kategoriKeluhan],
  'skala_nyeri': instance.skalaNyeri,
  'tingkat_kesadaran': _$TingkatKesadaranEnumMap[instance.tingkatKesadaran]!,
  'tanda_vital': instance.tandaVital,
  'sumber_tanda_vital': _$SumberTandaVitalEnumMap[instance.sumberTandaVital]!,
  'risk_level': _$RiskLevelEnumMap[instance.riskLevel]!,
  'sumber_rekomendasi': _$SumberRekomendasiEnumMap[instance.sumberRekomendasi]!,
  'penjelasan_ai': instance.penjelasanAi,
  'status_validasi': _$StatusValidasiEnumMap[instance.statusValidasi]!,
  'dibuat_oleh': instance.dibuatOleh,
  'divalidasi_oleh': instance.divalidasiOleh,
  'waktu_triase': instance.waktuTriase.toIso8601String(),
  'peringatan': instance.peringatan,
  'catatan_validasi_terakhir': instance.catatanValidasiTerakhir,
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

const _$TingkatKesadaranEnumMap = {
  TingkatKesadaran.a: 'A',
  TingkatKesadaran.v: 'V',
  TingkatKesadaran.p: 'P',
  TingkatKesadaran.u: 'U',
  TingkatKesadaran.$unknown: r'$unknown',
};

const _$SumberTandaVitalEnumMap = {
  SumberTandaVital.manual: 'manual',
  SumberTandaVital.pemindaian: 'pemindaian',
  SumberTandaVital.campuran: 'campuran',
  SumberTandaVital.$unknown: r'$unknown',
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
