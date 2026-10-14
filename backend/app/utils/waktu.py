"""Bantuan waktu. IGD berada di zona WIB, jadi batas hari dan usia dihitung dalam Asia/Jakarta."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

WIB = ZoneInfo("Asia/Jakarta")


def sekarang() -> datetime:
    return datetime.now(WIB)


def hari_ini() -> date:
    return sekarang().date()


def hitung_usia(tanggal_lahir: date, pada: date) -> int:
    """Usia dalam tahun penuh pada tanggal tertentu."""
    usia = pada.year - tanggal_lahir.year
    if (pada.month, pada.day) < (tanggal_lahir.month, tanggal_lahir.day):
        usia -= 1
    return usia


def usia_pasien(tanggal_lahir: date | None, perkiraan_usia: int | None, pada: date | None = None) -> int | None:
    """Usia dari tanggal lahir bila ada, selain itu dari perkiraan usia saat registrasi."""
    if tanggal_lahir is not None:
        return hitung_usia(tanggal_lahir, pada or hari_ini())
    return perkiraan_usia
