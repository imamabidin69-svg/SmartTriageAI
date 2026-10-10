"""Model SQLAlchemy untuk delapan tabel PDM SKPL v3.0."""

from app.models.konfigurasi import KONFIGURASI_BAWAAN, Konfigurasi
from app.models.kunjungan import Kunjungan
from app.models.log_audit import LogAudit
from app.models.pasien import Pasien
from app.models.pemindaian_alat import PemindaianAlat
from app.models.pengguna import Pengguna
from app.models.sesi_eir import SesiEir
from app.models.triase import Triase

__all__ = [
    "KONFIGURASI_BAWAAN",
    "Konfigurasi",
    "Kunjungan",
    "LogAudit",
    "Pasien",
    "PemindaianAlat",
    "Pengguna",
    "SesiEir",
    "Triase",
]
