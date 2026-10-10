"""Perintah CLI tambahan. Jalankan dengan: flask seed-demo"""

import os

import click
from flask import Flask
from flask.cli import with_appcontext
from sqlalchemy import select

from app.extensions import db
from app.models import Pengguna
from app.models.enums import Peran

PANJANG_MINIMAL_PASSWORD = 8

# Akun demo untuk tiga peran. Data simulasi, bukan data pegawai sungguhan.
# Password tidak ditulis di repo: diambil dari environment variable di .env.
AKUN_DEMO = (
    (Peran.ADMIN, "Siti Aminah", "admin@smarttriage.demo", "SEED_PASSWORD_ADMIN"),
    (Peran.PERAWAT, "Ns. Ratna Wijaya", "perawat@smarttriage.demo", "SEED_PASSWORD_PERAWAT"),
    (Peran.DOKTER, "dr. Bagus Kurniawan", "dokter@smarttriage.demo", "SEED_PASSWORD_DOKTER"),
)


@click.command("seed-demo")
@with_appcontext
def seed_demo() -> None:
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


def daftarkan_perintah(app: Flask) -> None:
    app.cli.add_command(seed_demo)
