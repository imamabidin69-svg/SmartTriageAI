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
from app.models.enums import JenisKelamin, Peran, TingkatKesadaran
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
EMAIL_DOKTER_DEMO = "dokter@smarttriage.demo"

# Pasien simulasi untuk demo papan prioritas ICU (8 bed). Nama fiktif, tanpa NIK dan nomor telepon.
# Setiap pasien: nama, perkiraan usia, jenis kelamin, bed, asal ruangan, diagnosis masuk, menit sejak masuk,
# lalu daftar observasi dari yang terlama. Observasi: (menit lalu, kesadaran, oksigen, (sistolik, diastolik,
# nadi, napas, suhu, saturasi), lab, setujui). Lab berisi laktat, kreatinin, trombosit, leukosit, bilirubin
# (boleh None). "setujui" berarti dokter demo sudah menyetujui penilaian itu.
A, V, P = TingkatKesadaran.SADAR_PENUH, TingkatKesadaran.RESPONS_SUARA, TingkatKesadaran.RESPONS_NYERI
TANPA_LAB = (None, None, None, None, None)
PASIEN_SIMULASI = (
    (
        "Agus Prasetyo",
        67,
        JenisKelamin.LAKI_LAKI,
        "ICU-1",
        "IGD",
        "Syok sepsis ec pneumonia",
        540,
        (
            (500, A, False, (124, 76, 92, 19, "37.4", "97"), ("1.4", "1.00", 220, "10.5", "0.7"), True),
            (25, V, True, (86, 48, 128, 27, "39.1", "90"), ("4.6", "2.10", 95, "19.8", "1.8"), False),
        ),
    ),
    (
        "Sri Wahyuni",
        54,
        JenisKelamin.PEREMPUAN,
        "ICU-2",
        "Kamar operasi",
        "Pasca laparotomi peritonitis",
        300,
        (
            (280, A, True, (118, 70, 96, 20, "37.6", "96"), ("1.8", "1.00", 210, "12.5", None), True),
            (50, A, True, (102, 60, 112, 23, "38.3", "94"), ("2.9", "1.30", 160, "16.1", None), False),
        ),
    ),
    (
        "Bambang Hartono",
        72,
        JenisKelamin.LAKI_LAKI,
        "ICU-3",
        "IGD",
        "Gagal jantung akut, edema paru",
        720,
        (
            (700, A, True, (150, 90, 108, 26, "36.7", "91"), ("2.2", "1.80", 230, "9.4", "0.9"), True),
            (180, A, True, (134, 82, 96, 22, "36.6", "94"), ("1.6", "1.70", 225, "9.1", "0.9"), False),
        ),
    ),
    (
        "Dewi Lestari",
        35,
        JenisKelamin.PEREMPUAN,
        "ICU-4",
        "Rawat inap",
        "Pre-eklampsia berat pasca SC",
        420,
        ((400, A, False, (162, 104, 92, 18, "36.9", "97"), ("1.2", "0.90", 140, "11.0", "0.8"), True),),
    ),
    (
        "Hendra Saputra",
        46,
        JenisKelamin.LAKI_LAKI,
        "ICU-5",
        "Kamar operasi",
        "Pasca kraniotomi cedera kepala",
        200,
        ((140, P, True, (128, 76, 64, 14, "37.2", "98"), TANPA_LAB, True),),
    ),
    (
        "Rina Kusuma",
        29,
        JenisKelamin.PEREMPUAN,
        "ICU-6",
        "IGD",
        "Ketoasidosis diabetik",
        900,
        (
            (880, A, False, (100, 60, 118, 28, "37.0", "97"), ("3.1", "1.60", 260, "15.0", None), True),
            (90, A, False, (118, 72, 92, 18, "36.8", "98"), ("1.1", "1.10", 250, "10.2", None), False),
        ),
    ),
    (
        "Yusuf Hidayat",
        61,
        JenisKelamin.LAKI_LAKI,
        "ICU-7",
        "Rujukan rumah sakit lain",
        "Stroke perdarahan",
        600,
        ((210, A, False, (146, 88, 78, 16, "36.9", "97"), TANPA_LAB, True),),
    ),
    ("Lina Marlina", 63, JenisKelamin.PEREMPUAN, "ICU-8", "IGD", "Gagal napas, PPOK eksaserbasi akut", 6, ()),
)


def _isian_observasi(kesadaran, oksigen, vital, lab) -> TriaseInput:
    sistolik, diastolik, nadi, napas, suhu, saturasi = vital
    laktat, kreatinin, trombosit, leukosit, bilirubin = lab
    return TriaseInput(
        tingkat_kesadaran=kesadaran,
        oksigen_tambahan=oksigen,
        tanda_vital={
            "td_sistolik": sistolik,
            "td_diastolik": diastolik,
            "nadi": nadi,
            "laju_napas": napas,
            "suhu": Decimal(suhu),
            "saturasi": Decimal(saturasi),
        },
        lab={
            "laktat": None if laktat is None else Decimal(laktat),
            "kreatinin": None if kreatinin is None else Decimal(kreatinin),
            "trombosit": trombosit,
            "leukosit": None if leukosit is None else Decimal(leukosit),
            "bilirubin": None if bilirubin is None else Decimal(bilirubin),
        },
    )


def _isi_pasien_simulasi() -> None:
    """Membuat pasien ICU dan observasi simulasi lewat TriaseService, supaya penilaiannya sama dengan aplikasi."""
    perawat = db.session.scalar(select(Pengguna).where(Pengguna.email == EMAIL_PERAWAT_DEMO))
    dokter = db.session.scalar(select(Pengguna).where(Pengguna.email == EMAIL_DOKTER_DEMO))
    service = TriaseService(model_registry(), cache_konfigurasi())
    waktu = sekarang()
    for nama, usia, jenis_kelamin, bed, asal, diagnosis, menit_masuk, daftar_observasi in PASIEN_SIMULASI:
        if db.session.scalar(select(Pasien).where(Pasien.nama == nama)) is not None:
            click.echo(f"Lewati pasien simulasi {nama}: sudah ada.")
            continue
        pasien = Pasien(
            didaftarkan_oleh=perawat.id_pengguna, nama=nama, perkiraan_usia=usia, jenis_kelamin=jenis_kelamin
        )
        db.session.add(pasien)
        db.session.flush()
        kunjungan = Kunjungan(
            id_pasien=pasien.id_pasien,
            waktu_datang=waktu - timedelta(minutes=menit_masuk),
            nomor_bed=bed,
            asal_ruangan=asal,
            diagnosis_masuk=diagnosis,
        )
        db.session.add(kunjungan)
        db.session.commit()

        level = "belum dinilai"
        for menit, kesadaran, oksigen, vital, lab, setujui in daftar_observasi:
            triase = service.buat(kunjungan.id_kunjungan, _isian_observasi(kesadaran, oksigen, vital, lab), perawat)
            # Waktu observasi dimundurkan supaya papan memperlihatkan interval observasi yang berbeda-beda.
            triase.waktu_triase = waktu - timedelta(minutes=menit)
            db.session.commit()
            if setujui and triase.bisa_diputuskan():
                ValidasiService().validasi(triase.id_triase, ValidasiRequest(aksi="setujui"), dokter)
            level = triase.risk_level.value
        click.echo(f"Pasien simulasi {nama} ({bed}) dibuat, level terakhir {level}.")


@click.command("seed-demo")
@click.option("--dengan-pasien", is_flag=True, help="Tambahkan 8 pasien ICU simulasi beserta observasinya.")
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
