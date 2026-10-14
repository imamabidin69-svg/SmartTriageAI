"""Perintah CLI tambahan. Jalankan dengan: flask seed-demo [--dengan-pasien]"""

import os
from datetime import timedelta
from decimal import Decimal

import click
from flask import Flask
from flask.cli import with_appcontext
from sqlalchemy import select

from app.ai.registry import model_registry
from app.extensions import db
from app.models import Kunjungan, Pasien, Pengguna
from app.models.enums import JenisKelamin, KategoriKeluhan, Peran, TingkatKesadaran
from app.services.konfigurasi_service import cache_konfigurasi
from app.services.triase_service import TriaseService
from app.services.validasi_service import ValidasiService
from app.utils.schemas import TriaseInput, ValidasiRequest
from app.utils.waktu import sekarang

PANJANG_MINIMAL_PASSWORD = 8

# Akun demo untuk tiga peran. Data simulasi, bukan data pegawai sungguhan.
# Password tidak ditulis di repo: diambil dari environment variable di .env.
AKUN_DEMO = (
    (Peran.ADMIN, "Siti Aminah", "admin@smarttriage.demo", "SEED_PASSWORD_ADMIN"),
    (Peran.PERAWAT, "Ns. Ratna Wijaya", "perawat@smarttriage.demo", "SEED_PASSWORD_PERAWAT"),
    (Peran.DOKTER, "dr. Bagus Kurniawan", "dokter@smarttriage.demo", "SEED_PASSWORD_DOKTER"),
)
EMAIL_PERAWAT_DEMO = "perawat@smarttriage.demo"

# Pasien simulasi untuk demo daftar tunggu dan rekap. Nama fiktif, tanpa NIK dan nomor telepon.
# Kolom: nama, perkiraan usia, jenis kelamin, menit sejak datang, isian triase (None = belum ditriase).
# Isian boleh memuat "review" (alasan ajuan review perawat) dan "ulang" (triase ulang beberapa menit lalu),
# supaya daftar tunggu dan peringatan punya contoh untuk didemokan.
PASIEN_SIMULASI = (
    (
        "Agus Prasetyo",
        58,
        JenisKelamin.LAKI_LAKI,
        35,
        {
            "keluhan_utama": "Nyeri dada kiri",
            "gejala": "Nyeri dada kiri menjalar ke lengan sejak satu jam lalu, berkeringat dingin",
            "kategori_keluhan": KategoriKeluhan.NYERI_DADA,
            "skala_nyeri": 8,
            "tingkat_kesadaran": TingkatKesadaran.SADAR_PENUH,
            "tanda_vital": (165, 100, 118, 26, "37.0", "93.0"),
            "menit_triase": 30,
        },
    ),
    (
        "Dewi Lestari",
        34,
        JenisKelamin.PEREMPUAN,
        50,
        {
            "keluhan_utama": "Demam dan batuk",
            "gejala": "Demam tiga hari disertai batuk berdahak dan badan pegal",
            "kategori_keluhan": KategoriKeluhan.DEMAM,
            "skala_nyeri": 3,
            "tingkat_kesadaran": TingkatKesadaran.SADAR_PENUH,
            "tanda_vital": (118, 76, 96, 20, "38.6", "97.0"),
            "menit_triase": 45,
            "review": "Demam sudah tiga hari, mohon dicek dokter",
        },
    ),
    (
        "Rudi Hartono",
        72,
        JenisKelamin.LAKI_LAKI,
        20,
        {
            "keluhan_utama": "Sesak napas",
            "gejala": "Sesak napas memberat sejak pagi, riwayat penyakit paru",
            "kategori_keluhan": KategoriKeluhan.SESAK_NAPAS_ATAU_BATUK,
            "skala_nyeri": 2,
            "tingkat_kesadaran": TingkatKesadaran.RESPONS_SUARA,
            "tanda_vital": (150, 90, 124, 30, "37.4", "88.0"),
            "menit_triase": 18,
        },
    ),
    (
        "Sri Wahyuni",
        45,
        JenisKelamin.PEREMPUAN,
        75,
        {
            "keluhan_utama": "Luka sobek di tangan",
            "gejala": "Luka sobek di telapak tangan kiri terkena pisau dapur, perdarahan sudah berkurang",
            "kategori_keluhan": KategoriKeluhan.CEDERA_ATAU_LUKA,
            "skala_nyeri": 5,
            "tingkat_kesadaran": TingkatKesadaran.SADAR_PENUH,
            "tanda_vital": (124, 80, 88, 18, "36.7", "99.0"),
            "menit_triase": 70,
        },
    ),
    (
        "Bayu Saputra",
        27,
        JenisKelamin.LAKI_LAKI,
        12,
        {
            "keluhan_utama": "Nyeri perut kanan bawah",
            "gejala": "Nyeri perut kanan bawah sejak semalam, mual, tidak bisa makan",
            "kategori_keluhan": KategoriKeluhan.NYERI_PERUT,
            "skala_nyeri": 7,
            "tingkat_kesadaran": TingkatKesadaran.SADAR_PENUH,
            "tanda_vital": (126, 82, 104, 20, "37.9", "98.0"),
            "menit_triase": 10,
        },
    ),
    (
        "Hendra Gunawan",
        49,
        JenisKelamin.LAKI_LAKI,
        55,
        {
            "keluhan_utama": "Pusing",
            "gejala": "Pusing dan lemas sejak pagi, belum makan",
            "kategori_keluhan": KategoriKeluhan.PUSING,
            "skala_nyeri": 2,
            "tingkat_kesadaran": TingkatKesadaran.SADAR_PENUH,
            "tanda_vital": (122, 80, 84, 18, "36.8", "98.0"),
            "menit_triase": 50,
            "ulang": {
                "keluhan_utama": "Sesak napas dan nyeri dada",
                "gejala": "Saat menunggu mendadak sesak napas dan nyeri dada, keringat dingin",
                "kategori_keluhan": KategoriKeluhan.NYERI_DADA,
                "skala_nyeri": 7,
                "tingkat_kesadaran": TingkatKesadaran.SADAR_PENUH,
                "tanda_vital": (172, 104, 124, 28, "37.2", "91.0"),
                "menit_triase": 6,
            },
        },
    ),
    ("Lina Marlina", 63, JenisKelamin.PEREMPUAN, 5, None),
)


def _isian_triase(isian: dict) -> TriaseInput:
    sistolik, diastolik, nadi, napas, suhu, saturasi = isian["tanda_vital"]
    return TriaseInput(
        keluhan_utama=isian["keluhan_utama"],
        gejala=isian["gejala"],
        kategori_keluhan=isian["kategori_keluhan"],
        skala_nyeri=isian["skala_nyeri"],
        tingkat_kesadaran=isian["tingkat_kesadaran"],
        tanda_vital={
            "td_sistolik": sistolik,
            "td_diastolik": diastolik,
            "nadi": nadi,
            "laju_napas": napas,
            "suhu": Decimal(suhu),
            "saturasi": Decimal(saturasi),
        },
    )


def _isi_pasien_simulasi() -> None:
    """Membuat kunjungan dan triase simulasi lewat TriaseService, supaya rekomendasinya sama dengan aplikasi."""
    perawat = db.session.scalar(select(Pengguna).where(Pengguna.email == EMAIL_PERAWAT_DEMO))
    service = TriaseService(model_registry(), cache_konfigurasi())
    waktu = sekarang()
    for nama, perkiraan_usia, jenis_kelamin, menit_datang, isian in PASIEN_SIMULASI:
        if db.session.scalar(select(Pasien).where(Pasien.nama == nama)) is not None:
            click.echo(f"Lewati pasien simulasi {nama}: sudah ada.")
            continue
        pasien = Pasien(
            didaftarkan_oleh=perawat.id_pengguna,
            nama=nama,
            perkiraan_usia=perkiraan_usia,
            jenis_kelamin=jenis_kelamin,
        )
        db.session.add(pasien)
        db.session.flush()
        kunjungan = Kunjungan(id_pasien=pasien.id_pasien, waktu_datang=waktu - timedelta(minutes=menit_datang))
        db.session.add(kunjungan)
        db.session.commit()

        if isian is None:
            click.echo(f"Pasien simulasi {nama} dibuat (belum ditriase).")
            continue
        triase = service.buat(kunjungan.id_kunjungan, _isian_triase(isian), perawat)
        # Waktu triase dimundurkan supaya daftar tunggu memperlihatkan lama menunggu yang berbeda-beda.
        triase.waktu_triase = waktu - timedelta(minutes=isian["menit_triase"])
        db.session.commit()
        if "review" in isian:
            permintaan = ValidasiRequest(aksi="ajukan_review", alasan=isian["review"])
            ValidasiService().validasi(triase.id_triase, permintaan, perawat)
        if "ulang" in isian:
            awal = triase.risk_level
            triase = service.buat(kunjungan.id_kunjungan, _isian_triase(isian["ulang"]), perawat)
            triase.waktu_triase = waktu - timedelta(minutes=isian["ulang"]["menit_triase"])
            db.session.commit()
            click.echo(f"Triase ulang {nama}: {awal.value} menjadi {triase.risk_level.value}.")
        click.echo(f"Pasien simulasi {nama} dibuat, rekomendasi {triase.risk_level.value}.")


@click.command("seed-demo")
@click.option("--dengan-pasien", is_flag=True, help="Tambahkan pasien, kunjungan, dan triase simulasi.")
@with_appcontext
def seed_demo(dengan_pasien: bool) -> None:
    """Membuat akun demo admin, perawat, dan dokter. Aman dijalankan berulang kali."""
    kurang = [env for *_, env in AKUN_DEMO if len(os.environ.get(env, "")) < PANJANG_MINIMAL_PASSWORD]
    if kurang:
        raise click.ClickException(
            f"Isi password akun demo (minimal {PANJANG_MINIMAL_PASSWORD} karakter) di .env: {', '.join(kurang)}"
        )

    for peran, nama, email, env in AKUN_DEMO:
        if db.session.scalar(select(Pengguna).where(Pengguna.email == email)) is not None:
            click.echo(f"Lewati {email}: akun sudah ada.")
            continue
        pengguna = Pengguna(nama=nama, email=email, peran=peran)
        pengguna.atur_password(os.environ[env])
        db.session.add(pengguna)
        click.echo(f"Akun {peran.value} dibuat: {email}")
    db.session.commit()

    if dengan_pasien:
        _isi_pasien_simulasi()


def daftarkan_perintah(app: Flask) -> None:
    app.cli.add_command(seed_demo)
