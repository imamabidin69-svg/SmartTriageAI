"""Model Pydantic untuk request dan response API."""

import re
import uuid
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Annotated, Any, Literal

from email_validator import EmailNotValidError, validate_email
from flask_openapi3 import FileStorage
from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationInfo,
    field_validator,
    model_validator,
)
from pydantic_core import PydanticCustomError

from app.ai.klasifikasi import SKOR_MAKSIMUM_ATURAN
from app.models.enums import (
    AksiAudit,
    JenisAlat,
    JenisKelamin,
    JenisTriase,
    KategoriKeluhan,
    PengisiEir,
    Peran,
    RiskLevel,
    StatusKunjungan,
    StatusSesiEir,
    StatusValidasi,
    SumberRekomendasi,
    SumberTandaVital,
    TingkatKesadaran,
)
from app.utils.waktu import hari_ini

PANJANG_MAKS_EMAIL = 150


def normalisasi_email(nilai: str) -> str:
    """Memvalidasi email lalu mengubahnya ke bentuk baku (tanpa spasi, huruf kecil).

    Fungsi yang sama dipakai untuk pencarian akun dan kunci pembatas login, supaya variasi
    spasi atau huruf besar tidak dianggap sebagai email yang berbeda.
    """
    try:
        hasil = validate_email(nilai.strip(), check_deliverability=False)
    except EmailNotValidError as galat:
        raise PydanticCustomError("kustom_email", "Format email tidak valid.") from galat
    return hasil.normalized.lower()


Email = Annotated[str, StringConstraints(max_length=PANJANG_MAKS_EMAIL), AfterValidator(normalisasi_email)]


class SkemaDasar(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LoginRequest(SkemaDasar):
    email: Email
    password: str = Field(min_length=1, max_length=128)


class LoginHeader(BaseModel):
    """Aplikasi Flutter mengirim X-Client: mobile supaya token dikirim di body, bukan cookie."""

    model_config = ConfigDict(populate_by_name=True)

    x_client: Literal["web", "mobile"] = Field(
        "web",
        alias="X-Client",
        description="Jenis klien. Tanpa header ini klien dianggap web dan token disimpan di cookie HttpOnly.",
    )


class PenggunaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_pengguna: uuid.UUID
    nama: str
    email: str
    peran: Peran
    is_active: bool


class SesiResponse(BaseModel):
    """Respons login dan refresh. Token hanya diisi untuk klien mobile."""

    pengguna: PenggunaResponse
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: Literal["Bearer"] | None = None
    expires_in: int | None = Field(None, description="Umur access token dalam detik.")


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "gagal"]
    komponen: dict[str, Literal["ok", "gagal"]]


# ---------------------------------------------------------------- umum


def _kosong_jadi_none(nilai: Any) -> Any:
    """Isian teks opsional yang dikirim kosong ("") dianggap tidak diisi."""
    if isinstance(nilai, str) and not nilai.strip():
        return None
    return nilai


# Karakter kontrol ditolak di semua isian teks. NUL membuat PostgreSQL menolak query (500), sedangkan
# pemisah \x1c-\x1f lolos strip tetapi dianggap spasi oleh str.split(). Tab dan baris baru tetap boleh.
KARAKTER_KONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _tanpa_karakter_kontrol(nilai: str) -> str:
    if KARAKTER_KONTROL.search(nilai):
        raise PydanticCustomError("karakter_tidak_diizinkan", "Isian berisi karakter yang tidak diizinkan.")
    return nilai


def _rapikan_spasi(nilai: str) -> str:
    return " ".join(nilai.split())


def Teks(minimal: int, maksimal: int) -> Any:  # noqa: N802 (dipakai seperti tipe)
    return Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=minimal, max_length=maksimal),
        AfterValidator(_tanpa_karakter_kontrol),
    ]


class PenggunaRingkas(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_pengguna: uuid.UUID
    nama: str


class Peringatan(BaseModel):
    """Peringatan yang tidak menolak request, misalnya nilai tanda vital yang tidak wajar (Desain 2.3)."""

    field: str | None = Field(description="Path field yang bersangkutan, misalnya tanda_vital.saturasi.")
    pesan: str


# ---------------------------------------------------------------- pasien dan kunjungan (FR-02)


def _cek_nik(nilai: str) -> str:
    if not re.fullmatch(r"[0-9]{16}", nilai):
        raise PydanticCustomError("kustom_nik", "NIK harus 16 digit angka.")
    return nilai


def _cek_telepon(nilai: str) -> str:
    if not re.fullmatch(r"\+?[0-9][0-9 -]{5,19}", nilai):
        raise PydanticCustomError(
            "kustom_telepon", "Nomor telepon hanya boleh berisi angka, spasi, tanda hubung, dan tanda + di depan."
        )
    return nilai


def _cek_tanggal_lahir(nilai: date) -> date:
    if nilai > hari_ini():
        raise PydanticCustomError("kustom_tanggal_lahir", "Tanggal lahir tidak boleh melewati hari ini.")
    if nilai.year < hari_ini().year - 150:
        raise PydanticCustomError("kustom_tanggal_lahir", "Tanggal lahir terlalu jauh di masa lalu.")
    return nilai


Nik = Annotated[str, StringConstraints(strip_whitespace=True), AfterValidator(_cek_nik)]
NoTelepon = Annotated[str, StringConstraints(strip_whitespace=True, max_length=20), AfterValidator(_cek_telepon)]


class CariPasienQuery(BaseModel):
    q: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=2, max_length=120),
        AfterValidator(_tanpa_karakter_kontrol),
        Field(description="Potongan nama pasien, atau NIK lengkap 16 digit."),
    ]


class PasienRingkas(BaseModel):
    id_pasien: uuid.UUID
    nama: str
    jenis_kelamin: JenisKelamin
    tanggal_lahir: date | None
    perkiraan_usia: int | None
    usia: int | None
    nik_tersamar: str | None = Field(description="Hanya empat digit terakhir NIK yang ditampilkan.")
    id_kunjungan_aktif: uuid.UUID | None = Field(description="Kunjungan yang masih menunggu atau sedang ditangani.")


class DaftarPasienResponse(BaseModel):
    items: list[PasienRingkas]


FIELD_IDENTITAS = ("nama", "tanggal_lahir", "perkiraan_usia", "jenis_kelamin", "nik", "no_telepon")


class RegistrasiRequest(SkemaDasar):
    """Registrasi singkat (Desain Gambar 2.5).

    Bila id_pasien diisi, pasien lama dipakai dan isian identitas lain diabaikan tanpa divalidasi
    (keputusan K8), karena form bisa saja masih membawa isian dari pencarian sebelumnya. Bila tidak,
    nama, jenis kelamin, dan tanggal lahir atau perkiraan usia wajib diisi; pemeriksaan ini dilakukan
    KunjunganService supaya pesannya tetap per field.
    """

    id_pasien: uuid.UUID | None = None
    nama: Annotated[Teks(1, 120), AfterValidator(_rapikan_spasi)] | None = None
    tanggal_lahir: Annotated[date, AfterValidator(_cek_tanggal_lahir)] | None = None
    perkiraan_usia: Annotated[int, Field(ge=0, le=150)] | None = None
    jenis_kelamin: JenisKelamin | None = None
    nik: Annotated[Nik | None, BeforeValidator(_kosong_jadi_none)] = None
    no_telepon: Annotated[NoTelepon | None, BeforeValidator(_kosong_jadi_none)] = None

    @model_validator(mode="before")
    @classmethod
    def _abaikan_identitas_bila_pasien_dipilih(cls, data: Any) -> Any:
        if isinstance(data, dict) and data.get("id_pasien") not in (None, ""):
            return {kunci: nilai for kunci, nilai in data.items() if kunci not in FIELD_IDENTITAS}
        return data


class KunjunganDibuatResponse(BaseModel):
    id_kunjungan: uuid.UUID
    id_pasien: uuid.UUID
    pasien_baru: bool
    status: StatusKunjungan
    waktu_datang: datetime


class KunjunganPath(BaseModel):
    id_kunjungan: uuid.UUID


# ---------------------------------------------------------------- triase (FR-03, FR-05)


def _satu_desimal(nilai: Decimal) -> Decimal:
    # Kolom suhu dan saturasi NUMERIC dengan satu desimal; dibulatkan di sini supaya nilai yang
    # diklasifikasi sama dengan nilai yang tersimpan.
    return nilai.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def _tanpa_duplikat(nilai: list[uuid.UUID]) -> list[uuid.UUID]:
    if len(set(nilai)) != len(nilai):
        raise PydanticCustomError("kustom_duplikat", "ID pemindaian tidak boleh dikirim lebih dari sekali.")
    return nilai


class TandaVital(SkemaDasar):
    """Batas di sini adalah nilai yang mungkin dicatat (sama dengan CHECK di basis data).

    Nilai yang mungkin tetapi tidak wajar, misalnya saturasi 85%, tetap diterima lalu ditandai
    sebagai peringatan (Desain 2.3).
    """

    td_sistolik: Annotated[int, Field(ge=0, le=320)]
    td_diastolik: Annotated[int, Field(ge=0, le=200)]
    nadi: Annotated[int, Field(ge=0, le=300)]
    laju_napas: Annotated[int, Field(ge=0, le=80)]
    suhu: Annotated[Decimal, Field(ge=20, le=45), AfterValidator(_satu_desimal)]
    saturasi: Annotated[Decimal, Field(ge=0, le=100), AfterValidator(_satu_desimal)]


class TriaseInput(SkemaDasar):
    """Isian form triase (Desain Gambar 2.8). Kategori keluhan dan skala nyeri wajib (keputusan K3)."""

    keluhan_utama: Teks(1, 200)
    gejala: Teks(10, 2000)
    kategori_keluhan: KategoriKeluhan
    skala_nyeri: Annotated[int, Field(ge=0, le=10)]
    tingkat_kesadaran: TingkatKesadaran = Field(description="AVPU: A sadar penuh, V suara, P nyeri, U tidak respons.")
    tanda_vital: TandaVital
    id_pemindaian: Annotated[list[uuid.UUID], Field(max_length=4), AfterValidator(_tanpa_duplikat)] = Field(
        default_factory=list, description="Hasil POST /pemindaian yang nilainya dipakai di form ini."
    )


class TriasePath(BaseModel):
    id_triase: uuid.UUID


class TandaVitalResponse(BaseModel):
    td_sistolik: int
    td_diastolik: int
    nadi: int
    laju_napas: int
    suhu: float
    saturasi: float


class FaktorResponse(BaseModel):
    fitur: str | None
    label: str
    nilai: str | float | int | None
    kontribusi: float = Field(description="Nilai SHAP untuk hasil model, atau poin aturan untuk aturan cadangan.")
    arah: Literal["naik", "turun", "netral"] = Field(
        description=(
            "Untuk sumber model: naik berarti faktor ini mendukung level yang direkomendasikan, turun berarti "
            "melawannya. Untuk sumber aturan: naik berarti menambah poin risiko; netral bila tidak ada aturan "
            "yang terpicu."
        )
    )


class PenjelasanResponse(BaseModel):
    versi_model: str | None
    faktor: list[FaktorResponse]
    probabilitas: dict[RiskLevel, float] | None


class PasienTriase(BaseModel):
    id_pasien: uuid.UUID
    nama: str
    usia: int | None
    jenis_kelamin: JenisKelamin


class TriaseDetail(BaseModel):
    """Bentuk yang sama dipakai respons POST /kunjungan/{id}/triase dan GET /triase/{id}."""

    id_triase: uuid.UUID
    id_kunjungan: uuid.UUID
    jenis: JenisTriase
    pasien: PasienTriase
    keluhan_utama: str
    gejala: str
    kategori_keluhan: KategoriKeluhan | None
    skala_nyeri: int | None
    tingkat_kesadaran: TingkatKesadaran
    tanda_vital: TandaVitalResponse
    sumber_tanda_vital: SumberTandaVital
    risk_level: RiskLevel
    sumber_rekomendasi: SumberRekomendasi
    penjelasan_ai: PenjelasanResponse
    status_validasi: StatusValidasi
    dibuat_oleh: PenggunaRingkas
    divalidasi_oleh: PenggunaRingkas | None
    waktu_triase: datetime
    peringatan: list[Peringatan]
    catatan_validasi_terakhir: str | None = Field(description="Alasan koreksi atau ajuan review terakhir, bila ada.")


# ---------------------------------------------------------------- konfigurasi (FR-05, FR-07)


def _dua_desimal(nilai: Decimal) -> Decimal:
    # Dibakukan seperti kolom NUMERIC(3,2) supaya catatan audit selalu bertulis "0.85 -> 0.90".
    return nilai.quantize(Decimal("0.01")) + Decimal("0")


AmbangKonfigurasi = Annotated[int, Field(ge=1, le=SKOR_MAKSIMUM_ATURAN)]
BatasTunggu = Annotated[int, Field(ge=1, le=1440, description="Dalam menit.")]


class KonfigurasiPatch(SkemaDasar):
    """Perubahan sebagian. Urutan ambang dan batas tunggu diperiksa KonfigurasiService terhadap nilai tersimpan."""

    versi_model: Teks(1, 50) = Field(default=None)
    ambang_kritis: AmbangKonfigurasi = Field(default=None)
    ambang_tinggi: AmbangKonfigurasi = Field(default=None)
    ambang_sedang: AmbangKonfigurasi = Field(default=None)
    batas_tunggu_tinggi: BatasTunggu = Field(default=None)
    batas_tunggu_sedang: BatasTunggu = Field(default=None)
    batas_tunggu_rendah: BatasTunggu = Field(default=None)
    ambang_keyakinan: Annotated[Decimal, Field(ge=0, le=1, decimal_places=2), AfterValidator(_dua_desimal)] = Field(
        default=None
    )

    @model_validator(mode="after")
    def _minimal_satu_field(self) -> "KonfigurasiPatch":
        if not self.model_fields_set:
            raise PydanticCustomError("kustom_kosong", "Isi minimal satu pengaturan yang ingin diubah.")
        return self


class KonfigurasiResponse(BaseModel):
    versi_model: str
    ambang_kritis: int
    ambang_tinggi: int
    ambang_sedang: int
    batas_tunggu_tinggi: int
    batas_tunggu_sedang: int
    batas_tunggu_rendah: int
    ambang_keyakinan: float
    versi_model_termuat: str | None = Field(description="Versi bundle model yang sedang dimuat, null bila tidak ada.")


# ---------------------------------------------------------------- validasi (FR-06)

PANJANG_MINIMAL_ALASAN = 5
AKSI_BERALASAN = ("koreksi", "ajukan_review")
NAMA_AKSI = {"koreksi": "koreksi", "ajukan_review": "ajuan review"}


class ValidasiRequest(SkemaDasar):
    """Desain Gambar 2.17. Alasan wajib minimal lima karakter untuk koreksi dan ajuan review (NFR-06)."""

    aksi: Literal["setujui", "koreksi", "ajukan_review"]
    risk_level: RiskLevel | None = Field(
        default=None, validate_default=True, description="Level hasil koreksi. Hanya diisi untuk aksi koreksi."
    )
    alasan: Annotated[Teks(0, 500) | None, BeforeValidator(_kosong_jadi_none)] = Field(
        default=None,
        validate_default=True,
        description="Wajib minimal 5 karakter untuk koreksi dan ajuan review. Boleh diisi saat menyetujui.",
    )

    @field_validator("risk_level")
    @classmethod
    def _risk_level_hanya_untuk_koreksi(cls, nilai: RiskLevel | None, info: ValidationInfo) -> RiskLevel | None:
        aksi = info.data.get("aksi")
        if aksi == "koreksi" and nilai is None:
            raise PydanticCustomError("kustom_risk_level", "Risk level hasil koreksi wajib diisi.")
        if aksi in ("setujui", "ajukan_review") and nilai is not None:
            raise PydanticCustomError("kustom_risk_level", "Risk level hanya diisi untuk aksi koreksi.")
        return nilai

    @field_validator("alasan")
    @classmethod
    def _alasan_wajib(cls, nilai: str | None, info: ValidationInfo) -> str | None:
        aksi = info.data.get("aksi")
        if aksi in AKSI_BERALASAN and (nilai is None or len(nilai) < PANJANG_MINIMAL_ALASAN):
            raise PydanticCustomError(
                "kustom_alasan",
                "Alasan {aksi} wajib diisi minimal {minimal} karakter.",
                {"aksi": NAMA_AKSI[aksi], "minimal": PANJANG_MINIMAL_ALASAN},
            )
        return nilai


# ---------------------------------------------------------------- status kunjungan dan antrean (FR-07)


class StatusKunjunganRequest(SkemaDasar):
    status: Literal["ditangani", "selesai"] = Field(
        description="ditangani saat dokter mulai memeriksa, selesai saat pemeriksaan berakhir atau pasien batal."
    )


class StatusKunjunganResponse(BaseModel):
    id_kunjungan: uuid.UUID
    status: StatusKunjungan
    waktu_ditangani: datetime | None


class TriaseTerakhir(BaseModel):
    id_triase: uuid.UUID
    jenis: JenisTriase
    risk_level: RiskLevel
    status_validasi: StatusValidasi
    keluhan_utama: str
    waktu_triase: datetime


class ItemDaftarTunggu(BaseModel):
    id_kunjungan: uuid.UUID
    pasien: PasienTriase
    waktu_datang: datetime
    triase_terakhir: TriaseTerakhir | None
    lama_menunggu_menit: int = Field(description="Sejak triase terakhir, atau sejak datang bila belum ditriase.")
    batas_tunggu_menit: int | None = Field(description="Batas dari konfigurasi; null untuk kritis dan belum ditriase.")
    status_tanda: Literal["belum_ditriase", "perlu_triase_ulang", "normal"]
    menunggu_validasi: bool
    review_diajukan: bool


class DaftarTungguResponse(BaseModel):
    items: list[ItemDaftarTunggu]
    waktu_server: datetime


class PasienPeringatan(BaseModel):
    id_pasien: uuid.UUID
    nama: str


class ItemPeringatan(BaseModel):
    jenis: Literal["kritis_belum_divalidasi", "level_naik", "tanda_bahaya_eir"]
    id_kunjungan: uuid.UUID
    id_triase: uuid.UUID | None
    id_sesi: uuid.UUID | None
    pasien: PasienPeringatan
    risk_level: RiskLevel | None
    alasan: str
    waktu: datetime


class DaftarPeringatanResponse(BaseModel):
    items: list[ItemPeringatan]


# ---------------------------------------------------------------- staf dan password (FR-01)

PANJANG_MINIMAL_PASSWORD = 8
PANJANG_MAKSIMAL_PASSWORD = 128
Nama = Annotated[Teks(1, 120), AfterValidator(_rapikan_spasi)]


class StafRequest(SkemaDasar):
    """Desain Gambar 2.2. Password tidak dikirim admin; server membuat password sementara (K7)."""

    nama: Nama
    email: Email
    peran: Peran


class StafPatch(SkemaDasar):
    nama: Nama = Field(default=None)
    email: Email = Field(default=None)
    peran: Peran = Field(default=None)
    is_active: bool = Field(default=None)
    atur_ulang_password: bool = Field(
        default=False, description="true untuk membuat password sementara baru. Password dikirim sekali di respons."
    )

    @model_validator(mode="after")
    def _minimal_satu_field(self) -> "StafPatch":
        if not self.model_fields_set:
            raise PydanticCustomError("kustom_kosong", "Isi minimal satu data staf yang ingin diubah.")
        return self


class StafQuery(BaseModel):
    peran: Peran | None = None
    aktif: bool | None = None


class StafPath(BaseModel):
    id_pengguna: uuid.UUID


class StafResponse(PenggunaResponse):
    created_at: datetime


class StafDisimpanResponse(BaseModel):
    staf: StafResponse
    password_sementara: str | None = Field(
        description="Hanya diisi saat staf dibuat atau password diatur ulang. Tidak bisa dilihat lagi."
    )


class DaftarStafResponse(BaseModel):
    items: list[StafResponse]


Password = Annotated[str, Field(min_length=PANJANG_MINIMAL_PASSWORD, max_length=PANJANG_MAKSIMAL_PASSWORD)]


class GantiPasswordRequest(SkemaDasar):
    password_lama: str = Field(min_length=1, max_length=PANJANG_MAKSIMAL_PASSWORD)
    password_baru: Password

    @field_validator("password_baru")
    @classmethod
    def _beda_dari_lama(cls, nilai: str, info: ValidationInfo) -> str:
        if nilai == info.data.get("password_lama"):
            raise PydanticCustomError("kustom_password_sama", "Password baru harus berbeda dari password lama.")
        return nilai


# ---------------------------------------------------------------- riwayat, rekap, log audit (FR-09)


class HalamanQuery(BaseModel):
    kursor: str | None = Field(default=None, max_length=200, description="Dari kursor_berikutnya halaman sebelumnya.")
    ukuran: int = Field(default=20, ge=1, le=50)


class PasienPath(BaseModel):
    id_pasien: uuid.UUID


class KunjunganRiwayat(BaseModel):
    id_kunjungan: uuid.UUID
    waktu_datang: datetime
    waktu_ditangani: datetime | None
    status: StatusKunjungan


class ItemRiwayat(BaseModel):
    id_triase: uuid.UUID
    jenis: JenisTriase
    waktu_triase: datetime
    keluhan_utama: str
    kategori_keluhan: KategoriKeluhan | None
    risk_level: RiskLevel
    sumber_rekomendasi: SumberRekomendasi
    status_validasi: StatusValidasi
    tanda_vital: TandaVitalResponse
    dibuat_oleh: PenggunaRingkas
    divalidasi_oleh: PenggunaRingkas | None
    kunjungan: KunjunganRiwayat


class RiwayatResponse(BaseModel):
    pasien: PasienTriase
    items: list[ItemRiwayat]
    kursor_berikutnya: str | None = Field(description="null bila sudah halaman terakhir.")


class RekapQuery(BaseModel):
    dari: date | None = Field(default=None, description="YYYY-MM-DD (WIB). Bawaan: 6 hari sebelum sampai.")
    sampai: date | None = Field(default=None, description="YYYY-MM-DD (WIB), inklusif. Bawaan: hari ini.")
    format: Literal["json", "csv"] = "json"


class RekapResponse(BaseModel):
    dari: date
    sampai: date
    total_triase: int
    per_level: dict[RiskLevel, int]
    rata_tunggu_menit: dict[RiskLevel, float | None] = Field(
        description="Rata-rata menit dari datang sampai ditangani, menurut level triase terakhir kunjungan."
    )
    persen_koreksi: float | None = Field(description="Triase yang dikoreksi dokter dibagi semua triase, dalam persen.")
    triase_ulang: int
    akurasi_pemindaian: float | None = Field(
        description="Persen kolom hasil pemindaian yang sama dengan nilai konfirmasi perawat; null bila belum ada."
    )


class LogAuditQuery(BaseModel):
    dari: date | None = None
    sampai: date | None = None
    aksi: AksiAudit | None = None
    id_aktor: uuid.UUID | None = None
    id_triase: uuid.UUID | None = None
    kursor: str | None = Field(default=None, max_length=200)
    ukuran: int = Field(default=50, ge=1, le=50)


class ItemLogAudit(BaseModel):
    id_log: uuid.UUID
    waktu: datetime
    aksi: AksiAudit
    aktor: PenggunaRingkas
    id_triase: uuid.UUID | None
    level_sebelum: RiskLevel | None
    level_sesudah: RiskLevel | None
    catatan: str | None


class LogAuditResponse(BaseModel):
    items: list[ItemLogAudit]
    kursor_berikutnya: str | None


# ---------------------------------------------------------------- pemindaian layar alat (FR-04)


class UnggahFoto(BaseModel):
    """Desain Gambar 2.11. Foto JPEG atau PNG maksimal 5 MB, diproses di memori lalu dibuang."""

    jenis_alat: JenisAlat
    berkas: FileStorage = Field(description="Foto layar alat (JPEG atau PNG, maksimal 5 MB).")


class HasilPemindaianResponse(BaseModel):
    id_pemindaian: uuid.UUID = Field(description="Dikirim lewat field id_pemindaian di form triase.")
    jenis_alat: JenisAlat
    nilai: dict[str, int | float | None] = Field(
        description="Nilai per kolom tanda vital. null berarti kolom dibiarkan kosong untuk diisi manual."
    )
    keyakinan: dict[str, float | None] = Field(description="Keyakinan model per kolom, null bila tidak terbaca.")
    kolom_kosong: list[str]
    pembaca_tersedia: bool = Field(description="false bila model pembaca layar belum dimuat; semua kolom kosong.")


# ---------------------------------------------------------------- Eir (FR-08)


def _wajib_setuju(nilai: bool) -> bool:
    if nilai is not True:
        raise PydanticCustomError("kustom_setuju", "Persetujuan wajib diberikan sebelum memakai Eir.")
    return nilai


class RingkasanTriase(BaseModel):
    """Desain Gambar 2.23. Ringkasan dari LLM yang divalidasi sebelum menjadi draf form triase."""

    keluhan_utama: Teks(1, 200)
    gejala: Teks(1, 2000)
    onset: Teks(1, 200)
    kategori_keluhan: KategoriKeluhan


class TautanEirResponse(BaseModel):
    token: str = Field(description="Dikirim lewat body POST /eir/sesi.")
    url: str = Field(description="Alamat halaman Eir untuk kode QR. Token ada di fragmen (#t=), tidak tercatat di log.")
    kedaluwarsa: datetime


class BukaSesiEirRequest(SkemaDasar):
    token: str = Field(min_length=1, max_length=500)
    setuju: Annotated[bool, AfterValidator(_wajib_setuju)]
    pengisi: PengisiEir


class SesiEirPath(BaseModel):
    id_sesi: uuid.UUID


class SesiEirDibuatResponse(BaseModel):
    id_sesi: uuid.UUID
    token_sesi: str = Field(description="Dikirim lewat header X-Token-Eir pada pesan berikutnya.")
    kedaluwarsa: datetime
    pesan: str = Field(description="Pertanyaan pertama Eir.")


class PesanEirRequest(SkemaDasar):
    teks: Teks(1, 1000)


class UnggahSuara(BaseModel):
    berkas: FileStorage = Field(description="Rekaman suara (webm, ogg, mp3, m4a, atau wav, maksimal 5 MB).")


class BalasanEirResponse(BaseModel):
    status: StatusSesiEir
    pesan: str = Field(description="Pertanyaan berikutnya, penutup, atau arahan menemui perawat.")
    jumlah_jawaban: int
    boleh_selesai: bool = Field(description="true bila jawaban sudah cukup untuk menekan Selesai.")
    transkripsi: str | None = Field(None, description="Hasil ubah suara ke teks (khusus mode suara).")


class ItemTranskrip(BaseModel):
    peran: Literal["eir", "pengisi"]
    teks: str
    waktu: datetime


class RingkasanEirResponse(BaseModel):
    id_sesi: uuid.UUID
    id_kunjungan: uuid.UUID
    pengisi: PengisiEir
    status: StatusSesiEir
    waktu_persetujuan: datetime
    waktu_selesai: datetime | None
    tanda_bahaya: str | None
    ringkasan: RingkasanTriase | None = Field(description="Draf form triase; wajib diperiksa perawat sebelum dipakai.")
    transkrip: list[ItemTranskrip]
