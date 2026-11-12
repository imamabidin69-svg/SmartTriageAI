// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'item_daftar_tunggu.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ItemDaftarTunggu _$ItemDaftarTungguFromJson(Map<String, dynamic> json) =>
    ItemDaftarTunggu(
      idKunjungan: json['id_kunjungan'] as String,
      pasien: PasienTriase.fromJson(json['pasien'] as Map<String, dynamic>),
      nomorBed: json['nomor_bed'] as String?,
      diagnosisMasuk: json['diagnosis_masuk'] as String?,
      status: StatusKunjungan.fromJson(json['status'] as String),
      waktuDatang: DateTime.parse(json['waktu_datang'] as String),
      triaseTerakhir: json['triase_terakhir'] == null
          ? null
          : TriaseTerakhir.fromJson(
              json['triase_terakhir'] as Map<String, dynamic>,
            ),
      lamaMenungguMenit: (json['lama_menunggu_menit'] as num).toInt(),
      batasTungguMenit: (json['batas_tunggu_menit'] as num?)?.toInt(),
      statusTanda: ItemDaftarTungguStatusTanda.fromJson(
        json['status_tanda'] as String,
      ),
      menungguValidasi: json['menunggu_validasi'] as bool,
      reviewDiajukan: json['review_diajukan'] as bool,
      ringkasanEirSiap: json['ringkasan_eir_siap'] as bool,
    );

Map<String, dynamic> _$ItemDaftarTungguToJson(
  ItemDaftarTunggu instance,
) => <String, dynamic>{
  'id_kunjungan': instance.idKunjungan,
  'pasien': instance.pasien,
  'nomor_bed': instance.nomorBed,
  'diagnosis_masuk': instance.diagnosisMasuk,
  'status': _$StatusKunjunganEnumMap[instance.status]!,
  'waktu_datang': instance.waktuDatang.toIso8601String(),
  'triase_terakhir': instance.triaseTerakhir,
  'lama_menunggu_menit': instance.lamaMenungguMenit,
  'batas_tunggu_menit': instance.batasTungguMenit,
  'status_tanda': _$ItemDaftarTungguStatusTandaEnumMap[instance.statusTanda]!,
  'menunggu_validasi': instance.menungguValidasi,
  'review_diajukan': instance.reviewDiajukan,
  'ringkasan_eir_siap': instance.ringkasanEirSiap,
};

const _$StatusKunjunganEnumMap = {
  StatusKunjungan.menunggu: 'menunggu',
  StatusKunjungan.ditangani: 'ditangani',
  StatusKunjungan.selesai: 'selesai',
  StatusKunjungan.$unknown: r'$unknown',
};

const _$ItemDaftarTungguStatusTandaEnumMap = {
  ItemDaftarTungguStatusTanda.belumDinilai: 'belum_dinilai',
  ItemDaftarTungguStatusTanda.observasiTerlambat: 'observasi_terlambat',
  ItemDaftarTungguStatusTanda.normal: 'normal',
  ItemDaftarTungguStatusTanda.$unknown: r'$unknown',
};
