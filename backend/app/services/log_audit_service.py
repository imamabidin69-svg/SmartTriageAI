"""Pembacaan log audit oleh admin dengan filter dan paginasi kursor (waktu, id_log) (FR-09, K13)."""

from dataclasses import dataclass

from sqlalchemy import select, tuple_
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models import LogAudit
from app.services.rekap_service import batas_waktu
from app.utils.errors import ValidasiGagalError
from app.utils.kursor import Kursor
from app.utils.schemas import LogAuditQuery


@dataclass(frozen=True)
class HalamanLog:
    items: list[LogAudit]
    kursor_berikutnya: str | None


class LogAuditService:
    def ambil(self, filter_: LogAuditQuery) -> HalamanLog:
        kueri = (
            select(LogAudit)
            .options(joinedload(LogAudit.aktor))
            .order_by(LogAudit.waktu.desc(), LogAudit.id_log.desc())
            .limit(filter_.ukuran + 1)
        )
        if filter_.dari and filter_.sampai and filter_.dari > filter_.sampai:
            raise ValidasiGagalError([{"field": "dari", "pesan": "Tanggal awal tidak boleh melewati tanggal akhir."}])
        if filter_.dari:
            kueri = kueri.where(LogAudit.waktu >= batas_waktu(filter_.dari, filter_.dari)[0])
        if filter_.sampai:
            kueri = kueri.where(LogAudit.waktu < batas_waktu(filter_.sampai, filter_.sampai)[1])
        if filter_.aksi:
            kueri = kueri.where(LogAudit.aksi == filter_.aksi)
        if filter_.id_aktor:
            kueri = kueri.where(LogAudit.id_aktor == filter_.id_aktor)
        if filter_.id_triase:
            kueri = kueri.where(LogAudit.id_triase == filter_.id_triase)
        if filter_.kursor:
            posisi = Kursor.dekode(filter_.kursor)
            kueri = kueri.where(tuple_(LogAudit.waktu, LogAudit.id_log) < (posisi.waktu, posisi.id))

        baris = list(db.session.scalars(kueri).unique())
        berikutnya = None
        if len(baris) > filter_.ukuran:
            baris = baris[: filter_.ukuran]
            berikutnya = Kursor(baris[-1].waktu, baris[-1].id_log).enkode()
        return HalamanLog(items=baris, kursor_berikutnya=berikutnya)
