"""Peringatan untuk perawat dan dokter (FR-07, Desain baris 293, keputusan K10).

Tiga jenis: triase kritis yang belum divalidasi, triase ulang yang levelnya naik, dan sesi Eir yang
dihentikan karena tanda bahaya tetapi belum diikuti triase baru. Hanya kunjungan yang masih menunggu
yang dihitung, sama dengan daftar tunggu; begitu dokter mulai memeriksa, peringatannya hilang.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import and_, exists, func, select

from app.extensions import db
from app.models import Kunjungan, Pasien, SesiEir, Triase
from app.models.enums import RiskLevel, StatusKunjungan, StatusSesiEir
from app.services.daftar_tunggu_service import STATUS_BELUM_DIVALIDASI, URUTAN_LEVEL

KRITIS_BELUM_DIVALIDASI = "kritis_belum_divalidasi"
LEVEL_NAIK = "level_naik"
TANDA_BAHAYA_EIR = "tanda_bahaya_eir"


@dataclass(frozen=True)
class Peringatan:
    jenis: str
    id_kunjungan: uuid.UUID
    id_pasien: uuid.UUID
    nama_pasien: str
    alasan: str
    waktu: datetime
    id_triase: uuid.UUID | None = None
    id_sesi: uuid.UUID | None = None
    risk_level: RiskLevel | None = None


class PeringatanService:
    def kumpulkan(self) -> list[Peringatan]:
        """Isinya sama untuk perawat dan dokter. Kritis lebih dulu, lalu yang terbaru."""
        hasil = self._dari_triase() + self._dari_eir()
        return sorted(hasil, key=lambda p: (p.jenis != KRITIS_BELUM_DIVALIDASI, -p.waktu.timestamp()))

    def _dari_triase(self) -> list[Peringatan]:
        urutan_terbaru = (Triase.waktu_triase.desc(), Triase.id_triase.desc())
        urutan_lama = (Triase.waktu_triase, Triase.id_triase)
        per_kunjungan = (
            select(
                Triase.id_triase,
                Triase.id_kunjungan,
                Triase.risk_level,
                Triase.status_validasi,
                Triase.waktu_triase,
                func.row_number().over(partition_by=Triase.id_kunjungan, order_by=urutan_terbaru).label("urut"),
                func.lag(Triase.risk_level)
                .over(partition_by=Triase.id_kunjungan, order_by=urutan_lama)
                .label("level_sebelumnya"),
            )
            .join(Kunjungan, Kunjungan.id_kunjungan == Triase.id_kunjungan)
            .where(Kunjungan.status == StatusKunjungan.MENUNGGU)
            .subquery()
        )
        baris = db.session.execute(
            select(per_kunjungan, Pasien.id_pasien, Pasien.nama)
            .join(Kunjungan, Kunjungan.id_kunjungan == per_kunjungan.c.id_kunjungan)
            .join(Pasien, Pasien.id_pasien == Kunjungan.id_pasien)
            .where(per_kunjungan.c.urut == 1, per_kunjungan.c.status_validasi.in_(STATUS_BELUM_DIVALIDASI))
        ).all()

        hasil = []
        for b in baris:
            # lag() mengembalikan teks biasa, jadi diubah lagi ke RiskLevel.
            sebelumnya = None if b.level_sebelumnya is None else RiskLevel(b.level_sebelumnya)
            naik = sebelumnya is not None and URUTAN_LEVEL[b.risk_level] > URUTAN_LEVEL[sebelumnya]
            # Satu peringatan per triase (U5): triase ulang yang naik menjadi kritis cukup muncul sebagai kritis.
            if b.risk_level == RiskLevel.KRITIS:
                jenis = KRITIS_BELUM_DIVALIDASI
                if naik:
                    alasan = f"Triase ulang naik dari {sebelumnya.value} ke kritis dan belum divalidasi."
                else:
                    alasan = "Hasil triase kritis belum divalidasi."
            elif naik:
                jenis = LEVEL_NAIK
                alasan = f"Triase ulang naik dari {sebelumnya.value} ke {b.risk_level.value} dan belum divalidasi."
            else:
                continue
            hasil.append(
                Peringatan(
                    jenis=jenis,
                    id_kunjungan=b.id_kunjungan,
                    id_pasien=b.id_pasien,
                    nama_pasien=b.nama,
                    alasan=alasan,
                    waktu=b.waktu_triase,
                    id_triase=b.id_triase,
                    risk_level=b.risk_level,
                )
            )
        return hasil

    def _dari_eir(self) -> list[Peringatan]:
        # Sesi dianggap sudah ditindaklanjuti bila ada triase pada kunjungan yang sama setelah sesi berhenti.
        waktu_berhenti = func.coalesce(SesiEir.waktu_selesai, SesiEir.waktu_persetujuan)
        sudah_ditriase = exists().where(
            and_(Triase.id_kunjungan == SesiEir.id_kunjungan, Triase.waktu_triase >= waktu_berhenti)
        )
        baris = db.session.execute(
            select(SesiEir, Pasien.id_pasien, Pasien.nama, waktu_berhenti.label("waktu_berhenti"))
            .join(Kunjungan, Kunjungan.id_kunjungan == SesiEir.id_kunjungan)
            .join(Pasien, Pasien.id_pasien == Kunjungan.id_pasien)
            .where(
                Kunjungan.status == StatusKunjungan.MENUNGGU,
                SesiEir.status == StatusSesiEir.DIHENTIKAN,
                SesiEir.tanda_bahaya.is_not(None),
                ~sudah_ditriase,
            )
        ).all()
        return [
            Peringatan(
                jenis=TANDA_BAHAYA_EIR,
                id_kunjungan=sesi.id_kunjungan,
                id_pasien=id_pasien,
                nama_pasien=nama,
                alasan=f"Eir menghentikan sesi karena tanda bahaya: {sesi.tanda_bahaya}",
                waktu=berhenti,
                id_sesi=sesi.id_sesi,
            )
            for sesi, id_pasien, nama, berhenti in baris
        ]
