"""Constraint basis data sesuai PDM SKPL v3.0 dan Desain Arsitektur Backend Bab 5."""

import uuid
from datetime import date
from decimal import Decimal

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from app.models import Konfigurasi, Kunjungan, LogAudit, Pasien, PemindaianAlat, Pengguna, SesiEir, Triase
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


def triase_valid(kunjungan: Kunjungan, **ubah) -> Triase:
    nilai = {
        "id_kunjungan": kunjungan.id_kunjungan,
        "jenis": JenisTriase.AWAL,
        "dibuat_oleh": kunjungan.pasien.didaftarkan_oleh,
        "keluhan_utama": "Demam dan batuk",
        "gejala": "Demam dua hari disertai batuk berdahak.",
        "kategori_keluhan": KategoriKeluhan.MUAL_MUNTAH_ATAU_DIARE,
        "skala_nyeri": 3,
        "tingkat_kesadaran": TingkatKesadaran.SADAR_PENUH,
        "td_sistolik": 120,
        "td_diastolik": 80,
        "nadi": 90,
        "laju_napas": 20,
        "suhu": Decimal("38.2"),
        "saturasi": Decimal("97.0"),
        "sumber_tanda_vital": SumberTandaVital.MANUAL,
        "risk_level": RiskLevel.SEDANG,
        "sumber_rekomendasi": SumberRekomendasi.MODEL,
        "penjelasan_ai": {"faktor": [{"label": "Suhu tubuh 38,2 °C", "arah": "meningkatkan"}]},
    }
    nilai.update(ubah)
    return Triase(**nilai)


def _simpan_dalam_savepoint(sesi, objek) -> None:
    with sesi.begin_nested():
        sesi.add(objek)
        sesi.flush()


def simpan_gagal(sesi, objek, constraint: str) -> None:
    with pytest.raises(IntegrityError) as galat:
        _simpan_dalam_savepoint(sesi, objek)
    assert galat.value.orig.diag.constraint_name == constraint


def test_triase_valid_tersimpan_dengan_nilai_bawaan(sesi_db, kunjungan):
    triase = triase_valid(kunjungan)
    sesi_db.add(triase)
    sesi_db.commit()
    sesi_db.refresh(triase)
    assert triase.status_validasi == StatusValidasi.MENUNGGU
    assert triase.waktu_triase is not None
    assert triase.waktu_triase.tzinfo is not None
    assert triase.kategori_keluhan == KategoriKeluhan.MUAL_MUNTAH_ATAU_DIARE
    assert triase.penjelasan_ai["faktor"][0]["label"] == "Suhu tubuh 38,2 °C"
    assert kunjungan.triase == [triase]


def test_saturasi_tidak_wajar_tetap_diterima(sesi_db, kunjungan):
    # Desain 2.3: nilai yang mungkin tetapi tidak wajar (saturasi 85%) tidak ditolak.
    sesi_db.add(triase_valid(kunjungan, saturasi=Decimal("85.0"), nadi=140))
    sesi_db.commit()


@pytest.mark.parametrize(
    ("kolom", "nilai", "constraint"),
    [
        ("saturasi", Decimal("100.5"), "ck_saturasi"),
        ("saturasi", Decimal("-1"), "ck_saturasi"),
        ("td_sistolik", 321, "ck_triase_td_sistolik"),
        ("td_diastolik", 201, "ck_triase_td_diastolik"),
        ("nadi", 301, "ck_triase_nadi"),
        ("laju_napas", 81, "ck_triase_laju_napas"),
        ("suhu", Decimal("19.9"), "ck_triase_suhu"),
        ("suhu", Decimal("45.1"), "ck_triase_suhu"),
        ("td_sistolik", -1, "ck_triase_td_sistolik"),
        ("nadi", -1, "ck_triase_nadi"),
        ("laju_napas", -1, "ck_triase_laju_napas"),
        ("skala_nyeri", 11, "ck_triase_skala_nyeri"),
        ("skala_nyeri", -1, "ck_triase_skala_nyeri"),
        ("gejala", "pendek", "ck_triase_gejala"),
        ("gejala", "x" * 2001, "ck_triase_gejala"),
    ],
)
def test_triase_di_luar_rentang_ditolak(sesi_db, kunjungan, kolom, nilai, constraint):
    simpan_gagal(sesi_db, triase_valid(kunjungan, **{kolom: nilai}), constraint)


@pytest.mark.parametrize(
    ("kolom", "nilai"),
    [
        ("saturasi", Decimal("100.0")),
        ("saturasi", Decimal("0")),
        ("suhu", Decimal("20.0")),
        ("suhu", Decimal("45.0")),
        ("td_sistolik", 0),
        ("td_sistolik", 320),
        ("td_diastolik", 0),
        ("td_diastolik", 200),
        ("nadi", 0),
        ("nadi", 300),
        ("laju_napas", 0),
        ("laju_napas", 80),
        ("skala_nyeri", 0),
        ("skala_nyeri", 10),
        ("skala_nyeri", None),
        ("gejala", "x" * 10),
        ("gejala", "x" * 2000),
    ],
)
def test_nilai_tepat_di_batas_rentang_diterima(sesi_db, kunjungan, kolom, nilai):
    _simpan_dalam_savepoint(sesi_db, triase_valid(kunjungan, **{kolom: nilai}))


def test_kunjungan_baru_berstatus_menunggu(sesi_db, kunjungan):
    sesi_db.refresh(kunjungan)
    assert kunjungan.status == StatusKunjungan.MENUNGGU
    assert kunjungan.waktu_datang is not None
    assert kunjungan.pasien.kunjungan == [kunjungan]


def _pasien(pendaftar: Pengguna, **ubah) -> Pasien:
    nilai = {
        "didaftarkan_oleh": pendaftar.id_pengguna,
        "nama": "Pasien Simulasi",
        "tanggal_lahir": date(1990, 1, 1),
        "jenis_kelamin": JenisKelamin.LAKI_LAKI,
    }
    nilai.update(ubah)
    return Pasien(**nilai)


def test_nik_unik_bila_diisi(sesi_db, buat_pengguna):
    perawat = buat_pengguna(Peran.PERAWAT)
    sesi_db.add_all([_pasien(perawat, nik=None), _pasien(perawat, nik=None), _pasien(perawat, nik="3519010101900001")])
    sesi_db.commit()
    simpan_gagal(sesi_db, _pasien(perawat, nik="3519010101900001"), "uq_pasien_nik")


@pytest.mark.parametrize(
    ("ubah", "constraint"),
    [
        ({"nik": "35190101019000AB"}, "ck_pasien_nik_format"),
        ({"tanggal_lahir": None, "perkiraan_usia": None}, "ck_pasien_tanggal_lahir_atau_usia"),
        ({"tanggal_lahir": None, "perkiraan_usia": 200}, "ck_pasien_perkiraan_usia"),
    ],
)
def test_pasien_tidak_valid_ditolak(sesi_db, buat_pengguna, ubah, constraint):
    simpan_gagal(sesi_db, _pasien(buat_pengguna(Peran.PERAWAT), **ubah), constraint)


def test_email_pengguna_wajib_huruf_kecil_dan_unik(sesi_db, buat_pengguna):
    pengguna = Pengguna(nama="Tes", email="Admin@SmartTriage.demo", peran=Peran.ADMIN, password_hash="x")
    simpan_gagal(sesi_db, pengguna, "ck_pengguna_email_huruf_kecil")
    buat_pengguna(Peran.ADMIN, email="admin-unik@smarttriage.demo")
    kembar = Pengguna(nama="Tes", email="admin-unik@smarttriage.demo", peran=Peran.ADMIN, password_hash="x")
    simpan_gagal(sesi_db, kembar, "uq_pengguna_email")


def test_password_disimpan_sebagai_hash_scrypt(buat_pengguna):
    pengguna = buat_pengguna(Peran.DOKTER, password="RahasiaDokter1")
    assert pengguna.password_hash.startswith("scrypt:")
    assert "RahasiaDokter1" not in pengguna.password_hash
    assert pengguna.cek_password("RahasiaDokter1")
    assert not pengguna.cek_password("salah")
    assert "dokter" in repr(pengguna)


@pytest.mark.parametrize("catatan", [None, "", "  abc  "])
def test_koreksi_dan_review_wajib_beralasan_minimal_lima_karakter(sesi_db, buat_pengguna, catatan):
    dokter = buat_pengguna(Peran.DOKTER)
    for aksi in (AksiAudit.KOREKSI, AksiAudit.AJUKAN_REVIEW):
        simpan_gagal(sesi_db, LogAudit(id_aktor=dokter.id_pengguna, aksi=aksi, catatan=catatan), "ck_alasan")


def test_alasan_empat_karakter_ditolak_lima_karakter_diterima(sesi_db, buat_pengguna):
    dokter = buat_pengguna(Peran.DOKTER)
    for aksi in (AksiAudit.KOREKSI, AksiAudit.AJUKAN_REVIEW):
        simpan_gagal(sesi_db, LogAudit(id_aktor=dokter.id_pengguna, aksi=aksi, catatan=" abcd "), "ck_alasan")
        _simpan_dalam_savepoint(sesi_db, LogAudit(id_aktor=dokter.id_pengguna, aksi=aksi, catatan="abcde"))


def test_log_audit_valid_tersimpan(sesi_db, kunjungan):
    triase = triase_valid(kunjungan)
    sesi_db.add(triase)
    sesi_db.flush()
    sesi_db.add_all(
        [
            LogAudit(
                id_aktor=triase.dibuat_oleh,
                id_triase=triase.id_triase,
                aksi=AksiAudit.KOREKSI,
                catatan="Nyeri dada khas, naikkan level",
                level_sebelum=RiskLevel.SEDANG,
                level_sesudah=RiskLevel.TINGGI,
            ),
            # Persetujuan tidak wajib beralasan.
            LogAudit(id_aktor=triase.dibuat_oleh, id_triase=triase.id_triase, aksi=AksiAudit.SETUJUI),
        ]
    )
    sesi_db.commit()
    jumlah = sesi_db.scalar(
        sa.select(sa.func.count()).select_from(LogAudit).where(LogAudit.id_triase == triase.id_triase)
    )
    assert jumlah == 2


def test_triase_yang_punya_log_audit_tidak_bisa_dihapus(sesi_db, kunjungan):
    # FK tanpa ON DELETE CASCADE: baris audit tidak boleh ikut hilang.
    triase = triase_valid(kunjungan)
    sesi_db.add(triase)
    sesi_db.flush()
    sesi_db.add(LogAudit(id_aktor=triase.dibuat_oleh, id_triase=triase.id_triase, aksi=AksiAudit.SETUJUI))
    sesi_db.commit()
    with pytest.raises(IntegrityError) as galat, sesi_db.begin_nested():
        sesi_db.execute(sa.delete(Triase).where(Triase.id_triase == triase.id_triase))
    assert galat.value.orig.diag.constraint_name == "fk_log_audit_id_triase_triase"


def test_konfigurasi_hanya_satu_baris_dan_ambang_berurutan(sesi_db):
    simpan_gagal(
        sesi_db,
        Konfigurasi(
            id_konfigurasi=2,
            versi_model="x",
            ambang_kritis=6,
            ambang_tinggi=4,
            ambang_sedang=2,
            batas_tunggu_tinggi=10,
            batas_tunggu_sedang=30,
            batas_tunggu_rendah=60,
            ambang_keyakinan=Decimal("0.85"),
        ),
        "ck_konfigurasi_satu_baris",
    )
    for kolom, nilai, constraint in (
        ("ambang_tinggi", 7, "ck_konfigurasi_ambang_berurutan"),
        ("batas_tunggu_tinggi", 45, "ck_konfigurasi_batas_tunggu"),
        ("ambang_keyakinan", Decimal("1.5"), "ck_konfigurasi_ambang_keyakinan"),
    ):
        with pytest.raises(IntegrityError) as galat, sesi_db.begin_nested():
            sesi_db.execute(sa.update(Konfigurasi).values({kolom: nilai}))
        assert galat.value.orig.diag.constraint_name == constraint


def test_pemindaian_alat_dan_sesi_eir(sesi_db, kunjungan):
    perawat_id = kunjungan.pasien.didaftarkan_oleh
    pemindaian = PemindaianAlat(
        dipindai_oleh=perawat_id,
        jenis_alat=JenisAlat.TENSIMETER,
        nilai_terbaca={"td_sistolik": 128, "td_diastolik": 84, "nadi": 88},
        keyakinan=Decimal("0.912"),
    )
    sesi = SesiEir(id_kunjungan=kunjungan.id_kunjungan, pengisi=PengisiEir.KELUARGA, waktu_persetujuan=sa.func.now())
    sesi_db.add_all([pemindaian, sesi])
    sesi_db.commit()
    sesi_db.refresh(sesi)
    assert pemindaian.id_triase is None
    assert sesi.status == StatusSesiEir.BERJALAN
    assert sesi.transkrip == []
    simpan_gagal(
        sesi_db,
        PemindaianAlat(
            dipindai_oleh=perawat_id, jenis_alat=JenisAlat.OKSIMETER, nilai_terbaca={}, keyakinan=Decimal("1.5")
        ),
        "ck_pemindaian_alat_keyakinan",
    )


def test_foreign_key_wajib_valid(sesi_db):
    simpan_gagal(sesi_db, Kunjungan(id_pasien=uuid.uuid4()), "fk_kunjungan_id_pasien_pasien")
