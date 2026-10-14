"""Penulis log audit (NFR-06, Desain Gambar 3.17).

Baris log selalu ditambahkan dalam transaksi yang sama dengan perubahan yang dicatat, dan tidak
pernah diubah atau dihapus. Role basis data aplikasi memang hanya punya hak SELECT dan INSERT.
"""

import uuid

from sqlalchemy.orm import Session, scoped_session

from app.extensions import db
from app.models import LogAudit, Pengguna
from app.models.enums import AksiAudit, RiskLevel


class AuditLogger:
    def __init__(self, sesi: Session | scoped_session | None = None) -> None:
        self.sesi = sesi if sesi is not None else db.session

    def catat(
        self,
        aksi: AksiAudit,
        aktor: Pengguna,
        id_triase: uuid.UUID | None = None,
        sebelum: RiskLevel | None = None,
        sesudah: RiskLevel | None = None,
        catatan: str | None = None,
    ) -> LogAudit:
        log = LogAudit(
            id_aktor=aktor.id_pengguna,
            id_triase=id_triase,
            aksi=aksi,
            catatan=catatan,
            level_sebelum=sebelum,
            level_sesudah=sesudah,
        )
        self.sesi.add(log)
        return log
