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
  nomorBed: json['nomor_bed'] as String?,
  statusKunjungan: StatusKunjungan.fromJson(json['status_kunjungan'] as String),
  tingkatKesadaran: TingkatKesadaran.fromJson(
    json['tingkat_kesadaran'] as String,
  ),
  oksigenTambahan: json['oksigen_tambahan'] as bool,
  tandaVital: TandaVitalResponse.fromJson(
    json['tanda_vital'] as Map<String, dynamic>,
  ),
  lab: HasilLabResponse.fromJson(json['lab'] as Map<String, dynamic>),
  ventilator: json['ventilator'] as bool,
  vasopresor: json['vasopresor'] as bool,
  catatan: json['catatan'] as String?,
  sumberTandaVital: SumberTandaVital.fromJson(
    json['sumber_tanda_vital'] as String,
  ),
  skorNews2: (json['skor_news2'] as num).toInt(),
  peluangPerburukan: json['peluang_perburukan'] as num?,
  levelSebelumnya: json['level_sebelumnya'] == null
      ? null
      : RiskLevel.fromJson(json['level_sebelumnya'] as String),
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
  'nomor_bed': instance.nomorBed,
  'status_kunjungan': _$StatusKunjunganEnumMap[instance.statusKunjungan]!,
  'tingkat_kesadaran': _$TingkatKesadaranEnumMap[instance.tingkatKesadaran]!,
  'oksigen_tambahan': instance.oksigenTambahan,
  'tanda_vital': instance.tandaVital,
  'lab': instance.lab,
  'ventilator': instance.ventilator,
  'vasopresor': instance.vasopresor,
  'catatan': instance.catatan,
  'sumber_tanda_vital': _$SumberTandaVitalEnumMap[instance.sumberTandaVital]!,
  'skor_news2': instance.skorNews2,
  'peluang_perburukan': instance.peluangPerburukan,
  'level_sebelumnya': _$RiskLevelEnumMap[instance.levelSebelumnya],
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

const _$StatusKunjunganEnumMap = {
  StatusKunjungan.menunggu: 'menunggu',
  StatusKunjungan.ditangani: 'ditangani',
  StatusKunjungan.selesai: 'selesai',
  StatusKunjungan.$unknown: r'$unknown',
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
  StatusValidasi.tercatat: 'tercatat',
  StatusValidasi.$unknown: r'$unknown',
};
