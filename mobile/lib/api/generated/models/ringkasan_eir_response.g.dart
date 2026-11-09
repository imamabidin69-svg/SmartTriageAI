// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'ringkasan_eir_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

RingkasanEirResponse _$RingkasanEirResponseFromJson(
  Map<String, dynamic> json,
) => RingkasanEirResponse(
  idSesi: json['id_sesi'] as String,
  idKunjungan: json['id_kunjungan'] as String,
  pengisi: PengisiEir.fromJson(json['pengisi'] as String),
  status: StatusSesiEir.fromJson(json['status'] as String),
  waktuPersetujuan: DateTime.parse(json['waktu_persetujuan'] as String),
  waktuSelesai: json['waktu_selesai'] == null
      ? null
      : DateTime.parse(json['waktu_selesai'] as String),
  tandaBahaya: json['tanda_bahaya'] as String?,
  ringkasan: json['ringkasan'] == null
      ? null
      : RingkasanTriase.fromJson(json['ringkasan'] as Map<String, dynamic>),
  transkrip: (json['transkrip'] as List<dynamic>)
      .map((e) => ItemTranskrip.fromJson(e as Map<String, dynamic>))
      .toList(),
);

Map<String, dynamic> _$RingkasanEirResponseToJson(
  RingkasanEirResponse instance,
) => <String, dynamic>{
  'id_sesi': instance.idSesi,
  'id_kunjungan': instance.idKunjungan,
  'pengisi': _$PengisiEirEnumMap[instance.pengisi]!,
  'status': _$StatusSesiEirEnumMap[instance.status]!,
  'waktu_persetujuan': instance.waktuPersetujuan.toIso8601String(),
  'waktu_selesai': instance.waktuSelesai?.toIso8601String(),
  'tanda_bahaya': instance.tandaBahaya,
  'ringkasan': instance.ringkasan,
  'transkrip': instance.transkrip,
};

const _$PengisiEirEnumMap = {
  PengisiEir.pasien: 'pasien',
  PengisiEir.keluarga: 'keluarga',
  PengisiEir.$unknown: r'$unknown',
};

const _$StatusSesiEirEnumMap = {
  StatusSesiEir.berjalan: 'berjalan',
  StatusSesiEir.selesai: 'selesai',
  StatusSesiEir.dihentikan: 'dihentikan',
  StatusSesiEir.$unknown: r'$unknown',
};
