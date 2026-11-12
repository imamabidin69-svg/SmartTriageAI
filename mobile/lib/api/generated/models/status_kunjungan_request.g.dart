// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'status_kunjungan_request.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

StatusKunjunganRequest _$StatusKunjunganRequestFromJson(
  Map<String, dynamic> json,
) => StatusKunjunganRequest(
  status: StatusKunjunganRequestStatus.fromJson(json['status'] as String),
);

Map<String, dynamic> _$StatusKunjunganRequestToJson(
  StatusKunjunganRequest instance,
) => <String, dynamic>{
  'status': _$StatusKunjunganRequestStatusEnumMap[instance.status]!,
};

const _$StatusKunjunganRequestStatusEnumMap = {
  StatusKunjunganRequestStatus.menunggu: 'menunggu',
  StatusKunjunganRequestStatus.ditangani: 'ditangani',
  StatusKunjunganRequestStatus.selesai: 'selesai',
  StatusKunjunganRequestStatus.$unknown: r'$unknown',
};
