/// Contoh respons API dalam bentuk JSON seperti yang dikirim backend, lalu dibaca dengan fromJson hasil generate.
library;

import 'package:smarttriage_mobile/api/generated/export.dart';

const idKunjungan = 'k0000000-0000-4000-8000-000000000001';
const idKunjunganDua = 'k0000000-0000-4000-8000-000000000002';
const idPasien = 'p0000000-0000-4000-8000-000000000001';
const idTriase = 't0000000-0000-4000-8000-000000000001';
const idTriaseKritis = 't0000000-0000-4000-8000-000000000002';
const idPemindaian = 's0000000-0000-4000-8000-000000000001';

Map<String, Object?> jsonPengguna(String peran) => {
  'id_pengguna': 'u-$peran',
  'nama': switch (peran) {
    'perawat' => 'Ns. Ratna Wijaya',
    'dokter' => 'dr. Bagus Kurniawan',
    _ => 'Siti Aminah',
  },
  'email': '$peran@smarttriage.demo',
  'peran': peran,
  'is_active': true,
};

PenggunaResponse pengguna(String peran) => PenggunaResponse.fromJson(jsonPengguna(peran));

Map<String, Object?> jsonPasien({String nama = 'Budi Santoso', String jk = 'laki_laki', int? usia = 45}) => {
  'id_pasien': idPasien,
  'nama': nama,
  'usia': usia,
  'jenis_kelamin': jk,
};

PasienTriase pasien() => PasienTriase.fromJson(jsonPasien());

Map<String, Object?> jsonItemTunggu({
  String id = idKunjungan,
  String nama = 'Budi Santoso',
  String? level = 'tinggi',
  String idTriaseTerakhir = idTriase,
  String statusValidasi = 'menunggu',
  String? bed = 'ICU-2',
  String? diagnosis = 'Syok sepsis',
  String status = 'menunggu',
  int skor = 6,
  double? peluang = 0.6512,
  int lama = 42,
  int? batas = 30,
  String tanda = 'observasi_terlambat',
  bool menungguValidasi = true,
  bool review = false,
  bool eirSiap = false,
}) => {
  'id_kunjungan': id,
  'pasien': jsonPasien(nama: nama),
  'nomor_bed': bed,
  'diagnosis_masuk': diagnosis,
  'status': status,
  'waktu_datang': '2026-11-02T01:42:00Z',
  'triase_terakhir': level == null
      ? null
      : {
          'id_triase': idTriaseTerakhir,
          'jenis': 'awal',
          'risk_level': level,
          'status_validasi': statusValidasi,
          'skor_news2': skor,
          'peluang_perburukan': peluang,
          'waktu_triase': '2026-11-02T01:50:00Z',
        },
  'lama_menunggu_menit': lama,
  'batas_tunggu_menit': batas,
  'status_tanda': tanda,
  'menunggu_validasi': menungguValidasi,
  'review_diajukan': review,
  'ringkasan_eir_siap': eirSiap,
};

DaftarTungguResponse daftarTunggu(List<Map<String, Object?>> items) =>
    DaftarTungguResponse.fromJson({'items': items, 'waktu_server': '2026-11-02T02:02:00Z'});

ItemPeringatan peringatan({
  String jenis = 'menunggu_persetujuan',
  String nama = 'Sri Wahyuni',
  String alasan = 'Level naik dari Tinggi ke Kritis dan menunggu persetujuan dokter.',
  String? idTriaseItem = idTriaseKritis,
  String idKunjunganItem = idKunjunganDua,
}) => ItemPeringatan.fromJson({
  'jenis': jenis,
  'id_kunjungan': idKunjunganItem,
  'id_triase': idTriaseItem,
  'id_sesi': jenis == 'informasi_penting_eir' ? 'sesi-1' : null,
  'pasien': {'id_pasien': 'p-2', 'nama': nama},
  'risk_level': jenis == 'informasi_penting_eir' ? null : 'kritis',
  'alasan': alasan,
  'waktu': '2026-11-02T01:58:00Z',
});

Map<String, Object?> jsonTriaseDetail({
  String id = idTriase,
  String level = 'tinggi',
  String status = 'menunggu',
  String sumber = 'model',
  List<Map<String, Object?>> peringatan = const [],
  String? divalidasi,
  String? catatan,
  String jenis = 'awal',
  String statusKunjungan = 'menunggu',
  String? levelSebelumnya,
  bool lab = true,
}) => {
  'id_triase': id,
  'id_kunjungan': idKunjungan,
  'jenis': jenis,
  'pasien': jsonPasien(),
  'nomor_bed': 'ICU-2',
  'status_kunjungan': statusKunjungan,
  'tingkat_kesadaran': 'A',
  'oksigen_tambahan': true,
  'lab': {
    'laktat': lab ? 3.4 : null,
    'kreatinin': lab ? 1.45 : null,
    'trombosit': lab ? 140 : null,
    'leukosit': null,
    'bilirubin': null,
  },
  'ventilator': false,
  'vasopresor': lab,
  'catatan': 'Urin 25 ml/jam',
  'skor_news2': 6,
  'peluang_perburukan': sumber == 'model' ? 0.6512 : null,
  'level_sebelumnya': levelSebelumnya,
  'tanda_vital': {
    'td_sistolik': 158,
    'td_diastolik': 96,
    'nadi': 104,
    'laju_napas': 22,
    'suhu': 37.2,
    'saturasi': 95.0,
  },
  'sumber_tanda_vital': 'campuran',
  'risk_level': level,
  'sumber_rekomendasi': sumber,
  'penjelasan_ai': {
    'versi_model': sumber == 'model' ? 'rf-icu-physionet2019-v1' : null,
    'skor_news2': 6,
    'level_news2': 'tinggi',
    'komponen_news2': [
      {
        'fitur': 'oksigen_tambahan',
        'label': 'Mendapat oksigen tambahan',
        'nilai': true,
        'kontribusi': 2,
        'arah': 'naik',
      },
      {'fitur': 'laju_napas', 'label': 'Laju napas 22 x/menit', 'nilai': 22, 'kontribusi': 2, 'arah': 'naik'},
      {'fitur': 'nadi', 'label': 'Nadi 104 x/menit', 'nilai': 104, 'kontribusi': 1, 'arah': 'naik'},
      {'fitur': 'saturasi', 'label': 'Saturasi oksigen 95%', 'nilai': 95.0, 'kontribusi': 1, 'arah': 'naik'},
    ],
    'peluang_perburukan': sumber == 'model' ? 0.6512 : null,
    'level_model': sumber == 'model' ? 'tinggi' : null,
    'faktor': sumber == 'model'
        ? [
            {'fitur': 'laktat', 'label': 'Laktat 3,4 mmol/L', 'nilai': 3.4, 'kontribusi': 0.21, 'arah': 'naik'},
            {'fitur': 'nadi', 'label': 'Nadi 104 x/menit', 'nilai': 104, 'kontribusi': 0.12, 'arah': 'naik'},
            {'fitur': 'usia', 'label': 'Usia 45 tahun', 'nilai': 45, 'kontribusi': -0.05, 'arah': 'turun'},
          ]
        : <Object>[],
  },
  'status_validasi': status,
  'dibuat_oleh': {'id_pengguna': 'u-perawat', 'nama': 'Ns. Ratna Wijaya'},
  'divalidasi_oleh': divalidasi == null ? null : {'id_pengguna': 'u-dokter', 'nama': divalidasi},
  'waktu_triase': '2026-11-02T01:50:00Z',
  'peringatan': peringatan,
  'catatan_validasi_terakhir': catatan,
};

TriaseDetail triaseDetail({
  String id = idTriase,
  String level = 'tinggi',
  String status = 'menunggu',
  String sumber = 'model',
  List<Map<String, Object?>> peringatan = const [],
  String? divalidasi,
  String? catatan,
  String jenis = 'awal',
  String statusKunjungan = 'menunggu',
  String? levelSebelumnya,
  bool lab = true,
}) => TriaseDetail.fromJson(
  jsonTriaseDetail(
    id: id,
    level: level,
    status: status,
    sumber: sumber,
    peringatan: peringatan,
    divalidasi: divalidasi,
    catatan: catatan,
    jenis: jenis,
    statusKunjungan: statusKunjungan,
    levelSebelumnya: levelSebelumnya,
    lab: lab,
  ),
);

PasienRingkas pasienRingkas({String nama = 'Budi Santoso', String? aktif, String? nik = '••••1234'}) =>
    PasienRingkas.fromJson({
      'id_pasien': idPasien,
      'nama': nama,
      'jenis_kelamin': 'laki_laki',
      'tanggal_lahir': '1981-03-02',
      'perkiraan_usia': null,
      'usia': 45,
      'nik_tersamar': nik,
      'id_kunjungan_aktif': aktif,
    });

KunjunganDibuatResponse kunjunganDibuat({bool baru = true}) => KunjunganDibuatResponse.fromJson({
  'id_kunjungan': idKunjungan,
  'id_pasien': idPasien,
  'pasien_baru': baru,
  'status': 'menunggu',
  'waktu_datang': '2026-11-02T01:42:00Z',
  'nomor_bed': 'ICU-2',
});

HasilPemindaianResponse hasilPemindaian({bool tersedia = true, bool kosongSemua = false}) =>
    HasilPemindaianResponse.fromJson({
      'id_pemindaian': idPemindaian,
      'jenis_alat': 'tensimeter',
      'nilai': kosongSemua
          ? {'td_sistolik': null, 'td_diastolik': null, 'nadi': null}
          : {'td_sistolik': 158, 'td_diastolik': 96, 'nadi': null},
      'keyakinan': kosongSemua
          ? {'td_sistolik': null, 'td_diastolik': null, 'nadi': null}
          : {'td_sistolik': 0.97, 'td_diastolik': 0.93, 'nadi': null},
      'kolom_kosong': kosongSemua ? ['td_sistolik', 'td_diastolik', 'nadi'] : ['nadi'],
      'pembaca_tersedia': tersedia,
    });

RingkasanEirResponse ringkasanEir({String status = 'selesai', bool denganRingkasan = true, String? tandaBahaya}) =>
    RingkasanEirResponse.fromJson({
      'id_sesi': 'sesi-1',
      'id_kunjungan': idKunjungan,
      'pengisi': 'keluarga',
      'status': status,
      'waktu_persetujuan': '2026-11-02T01:55:00Z',
      'waktu_selesai': status == 'berjalan' ? null : '2026-11-02T02:05:00Z',
      'tanda_bahaya': tandaBahaya,
      'ringkasan': denganRingkasan
          ? {
              'kronologi': 'Sesak sejak semalam lalu sulit dibangunkan',
              'riwayat_penyakit': 'Darah tinggi dan kencing manis',
              'obat_rutin': 'Amlodipin dan metformin',
              'alergi': 'Alergi amoxicillin',
              'informasi_lain': 'Tidak disebutkan',
            }
          : null,
      'transkrip': [
        {
          'peran': 'eir',
          'teks': 'Halo, saya Eir. Bisa diceritakan apa yang terjadi sebelum pasien dibawa ke rumah sakit?',
          'waktu': '2026-11-02T01:55:00Z',
        },
        {'peran': 'pengisi', 'teks': 'Sesak sejak semalam', 'waktu': '2026-11-02T01:56:00Z'},
      ],
    });

RiwayatResponse riwayat({String? kursor, String idTriaseItem = idTriase, int skor = 6}) => RiwayatResponse.fromJson({
  'pasien': jsonPasien(),
  'items': [
    {
      'id_triase': idTriaseItem,
      'jenis': 'ulang',
      'waktu_triase': '2026-11-02T01:50:00Z',
      'skor_news2': skor,
      'peluang_perburukan': 0.6512,
      'risk_level': 'tinggi',
      'sumber_rekomendasi': 'model',
      'status_validasi': 'disetujui',
      'tanda_vital': {
        'td_sistolik': 158,
        'td_diastolik': 96,
        'nadi': 104,
        'laju_napas': 22,
        'suhu': 37.2,
        'saturasi': 95.0,
      },
      'dibuat_oleh': {'id_pengguna': 'u-perawat', 'nama': 'Ns. Ratna Wijaya'},
      'divalidasi_oleh': null,
      'kunjungan': {
        'id_kunjungan': idKunjungan,
        'waktu_datang': '2026-11-02T01:42:00Z',
        'waktu_ditangani': null,
        'status': 'menunggu',
        'nomor_bed': 'ICU-2',
        'diagnosis_masuk': 'Syok sepsis',
      },
    },
  ],
  'kursor_berikutnya': kursor,
});

TautanEirResponse tautanEir() => TautanEirResponse.fromJson({
  'token': 'token-eir',
  'url': 'http://192.168.1.10:5000/eir#t=token-eir',
  'kedaluwarsa': '2026-11-02T04:00:00Z',
});

RiwayatResponse riwayatKosong() =>
    RiwayatResponse.fromJson({'pasien': jsonPasien(), 'items': <Object>[], 'kursor_berikutnya': null});
