"""Pemeriksaan kesehatan aplikasi (NFR-03, Desain Gambar 3.8 dan 3.9).

PostgreSQL adalah komponen wajib: bila gagal, health check membalas 503 supaya Railway
memulai ulang container. Komponen tidak wajib (model, sesi ONNX, Groq) ditambahkan di
tahap berikutnya dan hanya membuat status menjadi "degraded".
"""

import logging
from abc import ABC, abstractmethod
from collections.abc import Sequence

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.utils.schemas import HealthResponse

logger = logging.getLogger(__name__)


class PemeriksaKomponen(ABC):
    nama: str
    wajib: bool

    @abstractmethod
    def cek(self) -> bool:
        """True bila komponen sehat."""


class PemeriksaDatabase(PemeriksaKomponen):
    nama = "database"
    wajib = True

    def cek(self) -> bool:
        try:
            db.session.execute(text("SELECT 1"))
        except SQLAlchemyError:
            db.session.rollback()
            logger.warning("Health check: basis data tidak dapat dihubungi.", exc_info=True)
            return False
        return True


class PemeriksaHakAksesLogAudit(PemeriksaKomponen):
    """Memastikan aplikasi tidak berjalan dengan role yang bisa mengubah atau menghapus log_audit (NFR-06).

    Misalnya bila DATABASE_URL terisi role pemilik tabel. Komponen ini wajib, sehingga health check
    membalas 503 dan aplikasi tidak dianggap sehat sampai role basis datanya diperbaiki.
    """

    nama = "hak_akses_log_audit"
    wajib = True

    def cek(self) -> bool:
        try:
            bisa_mengubah = db.session.scalar(
                text(
                    "SELECT has_table_privilege('log_audit', 'UPDATE') "
                    "OR has_table_privilege('log_audit', 'DELETE') "
                    "OR has_table_privilege('log_audit', 'TRUNCATE')"
                )
            )
        except SQLAlchemyError:
            db.session.rollback()
            logger.warning("Health check: hak akses log_audit tidak dapat diperiksa.", exc_info=True)
            return False
        if bisa_mengubah:
            logger.error("Role basis data aplikasi masih bisa mengubah log_audit. Pakai role smarttriage_app.")
            return False
        return True


class HealthService:
    def __init__(self, pemeriksa: Sequence[PemeriksaKomponen]) -> None:
        self.pemeriksa = pemeriksa

    def periksa(self) -> HealthResponse:
        status = "ok"
        komponen: dict[str, str] = {}
        for pemeriksa in self.pemeriksa:
            try:
                sehat = pemeriksa.cek()
            except Exception:
                # Pemeriksa yang error dianggap gagal; rinciannya hanya masuk log server.
                logger.exception("Health check: pemeriksa %s error.", pemeriksa.nama)
                sehat = False
            komponen[pemeriksa.nama] = "ok" if sehat else "gagal"
            if not sehat:
                status = "gagal" if pemeriksa.wajib else ("degraded" if status == "ok" else status)
        return HealthResponse(status=status, komponen=komponen)
