"""Nilai ENUM basis data sesuai PDM SKPL v3.0 (Gambar 6.2) dan ERD Desain Backend (Gambar 5.1).

Setiap tipe ENUM PostgreSQL dideklarasikan sekali di sini lalu dipakai ulang oleh kolom
yang membutuhkannya, misalnya risk_level di tabel triase dan log_audit.
"""

from enum import StrEnum

import sqlalchemy as sa


class Peran(StrEnum):
    PERAWAT = "perawat"
    DOKTER = "dokter"
    ADMIN = "admin"


class JenisKelamin(StrEnum):
    LAKI_LAKI = "laki_laki"
    PEREMPUAN = "perempuan"


class StatusKunjungan(StrEnum):
    MENUNGGU = "menunggu"
    DITANGANI = "ditangani"
    SELESAI = "selesai"


class JenisTriase(StrEnum):
    AWAL = "awal"
    ULANG = "ulang"


class TopikAnamnesis(StrEnum):
    """Enam topik yang digali Eir dari keluarga pasien ICU. Hanya dipakai di Python, tidak ada tipe di basis data."""

    KRONOLOGI = "Kronologi sebelum masuk ICU"
    RIWAYAT_PENYAKIT = "Riwayat penyakit"
    OBAT_RUTIN = "Obat rutin"
    ALERGI = "Alergi"
    RIWAYAT_OPERASI = "Riwayat operasi dan rawat inap"
    KEBIASAAN = "Kebiasaan dan kondisi sehari-hari"


class TingkatKesadaran(StrEnum):
    """Skala AVPU."""

    SADAR_PENUH = "A"
    RESPONS_SUARA = "V"
    RESPONS_NYERI = "P"
    TIDAK_RESPONS = "U"


class SumberTandaVital(StrEnum):
    MANUAL = "manual"
    PEMINDAIAN = "pemindaian"
    CAMPURAN = "campuran"


class RiskLevel(StrEnum):
    RENDAH = "rendah"
    SEDANG = "sedang"
    TINGGI = "tinggi"
    KRITIS = "kritis"


class SumberRekomendasi(StrEnum):
    MODEL = "model"
    ATURAN = "aturan"


class StatusValidasi(StrEnum):
    MENUNGGU = "menunggu"
    DISETUJUI = "disetujui"
    MENUNGGU_REVIEW_DOKTER = "menunggu_review_dokter"
    DIKOREKSI = "dikoreksi"
    TERCATAT = "tercatat"


class JenisAlat(StrEnum):
    TENSIMETER = "tensimeter"
    OKSIMETER = "oksimeter"
    TERMOMETER = "termometer"
    BEDSIDE_MONITOR = "bedside_monitor"


class PengisiEir(StrEnum):
    PASIEN = "pasien"
    KELUARGA = "keluarga"


class StatusSesiEir(StrEnum):
    BERJALAN = "berjalan"
    SELESAI = "selesai"
    DIHENTIKAN = "dihentikan"


class AksiAudit(StrEnum):
    SETUJUI = "setujui"
    KOREKSI = "koreksi"
    AJUKAN_REVIEW = "ajukan_review"
    UBAH_KONFIGURASI = "ubah_konfigurasi"
    TAMBAH_STAF = "tambah_staf"
    UBAH_STAF = "ubah_staf"
    NONAKTIFKAN_STAF = "nonaktifkan_staf"
    AKTIFKAN_STAF = "aktifkan_staf"
    ATUR_ULANG_PASSWORD = "atur_ulang_password"  # noqa: S105 (nama aksi audit, bukan password)
    REGISTRASI_KUNJUNGAN = "registrasi_kunjungan"


def _nilai_enum(kelas: type[StrEnum]) -> list[str]:
    # Label di basis data memakai nilai enum (misalnya "Nyeri dada"), bukan nama member Python.
    return [anggota.value for anggota in kelas]


def _tipe_enum(kelas: type[StrEnum], nama: str) -> sa.Enum:
    return sa.Enum(kelas, name=nama, values_callable=_nilai_enum, validate_strings=True)


PERAN = _tipe_enum(Peran, "peran")
JENIS_KELAMIN = _tipe_enum(JenisKelamin, "jenis_kelamin")
STATUS_KUNJUNGAN = _tipe_enum(StatusKunjungan, "status_kunjungan")
JENIS_TRIASE = _tipe_enum(JenisTriase, "jenis_triase")
TINGKAT_KESADARAN = _tipe_enum(TingkatKesadaran, "tingkat_kesadaran")
SUMBER_TANDA_VITAL = _tipe_enum(SumberTandaVital, "sumber_tanda_vital")
RISK_LEVEL = _tipe_enum(RiskLevel, "risk_level")
SUMBER_REKOMENDASI = _tipe_enum(SumberRekomendasi, "sumber_rekomendasi")
STATUS_VALIDASI = _tipe_enum(StatusValidasi, "status_validasi")
JENIS_ALAT = _tipe_enum(JenisAlat, "jenis_alat")
PENGISI_EIR = _tipe_enum(PengisiEir, "pengisi_eir")
STATUS_SESI_EIR = _tipe_enum(StatusSesiEir, "status_sesi_eir")
AKSI_AUDIT = _tipe_enum(AksiAudit, "aksi_audit")

SEMUA_TIPE_ENUM = (
    PERAN,
    JENIS_KELAMIN,
    STATUS_KUNJUNGAN,
    JENIS_TRIASE,
    TINGKAT_KESADARAN,
    SUMBER_TANDA_VITAL,
    RISK_LEVEL,
    SUMBER_REKOMENDASI,
    STATUS_VALIDASI,
    JENIS_ALAT,
    PENGISI_EIR,
    STATUS_SESI_EIR,
    AKSI_AUDIT,
)
