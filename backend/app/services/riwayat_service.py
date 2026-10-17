"""Riwayat triase pasien dengan paginasi kursor (waktu_triase, id_triase) (FR-09, Desain 2.9, K13)."""

import uuid
from dataclasses import dataclass

from sqlalchemy import select, tuple_
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models import Kunjungan, Pasien, Triase
from app.utils.errors import TidakDitemukanError
from app.utils.kursor import Kursor


@dataclass(frozen=True)
class HalamanRiwayat:
    pasien: Pasien
    items: list[Triase]
    kursor_berikutnya: str | None


class RiwayatService:
    def ambil(self, id_pasien: uuid.UUID, kursor: str | None, ukuran: int) -> HalamanRiwayat:
        pasien = db.session.get(Pasien, id_pasien)
        if pasien is None:
            raise TidakDitemukanError("Pasien tidak ditemukan.")
        kueri = (
            select(Triase)
            .join(Kunjungan, Kunjungan.id_kunjungan == Triase.id_kunjungan)
            .where(Kunjungan.id_pasien == id_pasien)
            .options(joinedload(Triase.kunjungan), joinedload(Triase.pembuat), joinedload(Triase.validator))
            .order_by(Triase.waktu_triase.desc(), Triase.id_triase.desc())
            # Satu baris ekstra untuk mengetahui apakah masih ada halaman berikutnya.
            .limit(ukuran + 1)
        )
        if kursor is not None:
            posisi = Kursor.dekode(kursor)
            kueri = kueri.where(tuple_(Triase.waktu_triase, Triase.id_triase) < (posisi.waktu, posisi.id))
        baris = list(db.session.scalars(kueri).unique())
        berikutnya = None
        if len(baris) > ukuran:
            baris = baris[:ukuran]
            terakhir = baris[-1]
            berikutnya = Kursor(terakhir.waktu_triase, terakhir.id_triase).enkode()
        return HalamanRiwayat(pasien=pasien, items=baris, kursor_berikutnya=berikutnya)
