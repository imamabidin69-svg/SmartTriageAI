"""Pembatas percobaan gagal per akun, memakai penyimpanan Flask-Limiter yang sama dengan pembatas login.

Hitungan hanya ditambah setelah hasilnya diketahui gagal, jadi percobaan yang berhasil tidak dibatasi.
Dipakai untuk pencarian NIK yang tidak ditemukan dan ganti password dengan password lama yang salah.
"""

import math
import time

from flask import current_app
from limits import parse

from app.extensions import limiter
from app.models import Pengguna
from app.utils.errors import TerlaluBanyakPercobaanError


class PembatasPerAkun:
    def __init__(self, kunci_konfigurasi: str, awalan: str, pengguna: Pengguna, pesan: str) -> None:
        self.item = parse(current_app.config[kunci_konfigurasi])
        self.kunci = f"{awalan}:{pengguna.id_pengguna}"
        self.pesan = pesan

    def periksa(self) -> None:
        if not limiter.enabled or limiter.limiter.test(self.item, self.kunci):
            return
        reset = limiter.limiter.get_window_stats(self.item, self.kunci).reset_time
        raise TerlaluBanyakPercobaanError(self.pesan, max(1, math.ceil(reset - time.time())))

    def catat_gagal(self) -> None:
        if limiter.enabled:
            limiter.limiter.hit(self.item, self.kunci)
