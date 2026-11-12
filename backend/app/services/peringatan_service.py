"""Peringatan untuk perawat dan dokter ICU (FR-07, Desain baris 293, keputusan K10).

Tiga jenis: penilaian yang menunggu persetujuan dokter (penilaian awal atau level naik), observasi yang
terlambat dari intervalnya, dan informasi penting dari keluarga lewat Eir (misalnya alergi obat) yang belum
diikuti observasi baru. Hanya pasien yang masih di ICU yang dihitung, sama dengan papan prioritas.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import and_, exists, func, select

from app.extensions import db
from app.models import Kunjungan, Pasien, SesiEir, Triase
from app.models.enums import RiskLevel
from app.services.daftar_tunggu_service import STATUS_BELUM_DIVALIDASI, STATUS_DI_ICU, DaftarTungguService
from app.services.konfigurasi_service import NilaiKonfigurasi

MENUNGGU_PERSETUJUAN = "menunggu_persetujuan"
OBSERVASI_TERLAMBAT = "observasi_terlambat"
INFORMASI_PENTING_EIR = "informasi_penting_eir"
URUTAN_JENIS = (MENUNGGU_PERSETUJUAN, OBSERVASI_TERLAMBAT, INFORMASI_PENTING_EIR)
NAMA_LEVEL = {
    RiskLevel.KRITIS: "Kritis",
    RiskLevel.TINGGI: "Tinggi",
    RiskLevel.SEDANG: "Sedang",
    RiskLevel.RENDAH: "Rendah",
}


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
    def __init__(self, konfigurasi: NilaiKonfigurasi) -> None:
        self.konfigurasi = konfigurasi

    def kumpulkan(self, sekarang: datetime) -> list[Peringatan]:
        """Isinya sama untuk perawat dan dokter. Persetujuan Kritis lebih dulu, lalu per jenis, lalu terbaru."""
        hasil = self._menunggu_persetujuan() + self._observasi_terlambat(sekarang) + self._dari_eir()
        return sorted(
            hasil,
            key=lambda p: (
                not (p.jenis == MENUNGGU_PERSETUJUAN and p.risk_level == RiskLevel.KRITIS),
                URUTAN_JENIS.index(p.jenis),
                -p.waktu.timestamp(),
            ),
        )

    def _menunggu_persetujuan(self) -> list[Peringatan]:
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
            .where(Kunjungan.status.in_(STATUS_DI_ICU))
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
            level = NAMA_LEVEL[b.risk_level]
            if sebelumnya is None:
                alasan = f"Penilaian awal {level} menunggu persetujuan dokter."
            elif sebelumnya != b.risk_level:
                alasan = f"Level naik dari {NAMA_LEVEL[sebelumnya]} ke {level} dan menunggu persetujuan dokter."
            else:
                alasan = f"Level {level} belum disetujui dokter."
            hasil.append(
                Peringatan(
                    jenis=MENUNGGU_PERSETUJUAN,
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

    def _observasi_terlambat(self, sekarang: datetime) -> list[Peringatan]:
        hasil = []
        for item in DaftarTungguService(self.konfigurasi).susun(sekarang):
            triase = item.triase_terakhir
            if item.status_tanda != "observasi_terlambat" or triase is None:
                continue
            hasil.append(
                Peringatan(
                    jenis=OBSERVASI_TERLAMBAT,
                    id_kunjungan=item.kunjungan.id_kunjungan,
                    id_pasien=item.pasien.id_pasien,
                    nama_pasien=item.pasien.nama,
                    alasan=(
                        f"Observasi terakhir {item.lama_menunggu} menit lalu, melewati interval "
                        f"{item.batas_tunggu} menit untuk level {NAMA_LEVEL[triase.risk_level]}."
                    ),
                    waktu=triase.waktu_triase,
                    id_triase=triase.id_triase,
                    risk_level=triase.risk_level,
                )
            )
        return hasil

    def _dari_eir(self) -> list[Peringatan]:
        # Informasi dianggap sudah dibaca perawat bila ada observasi baru setelah sesi berhenti.
        waktu_berhenti = func.coalesce(SesiEir.waktu_selesai, SesiEir.waktu_persetujuan)
        sudah_diobservasi = exists().where(
            and_(Triase.id_kunjungan == SesiEir.id_kunjungan, Triase.waktu_triase >= waktu_berhenti)
        )
        baris = db.session.execute(
            select(SesiEir, Pasien.id_pasien, Pasien.nama, waktu_berhenti.label("waktu_berhenti"))
            .join(Kunjungan, Kunjungan.id_kunjungan == SesiEir.id_kunjungan)
            .join(Pasien, Pasien.id_pasien == Kunjungan.id_pasien)
            .where(
                Kunjungan.status.in_(STATUS_DI_ICU),
                SesiEir.tanda_bahaya.is_not(None),
                ~sudah_diobservasi,
            )
        ).all()
        return [
            Peringatan(
                jenis=INFORMASI_PENTING_EIR,
                id_kunjungan=sesi.id_kunjungan,
                id_pasien=id_pasien,
                nama_pasien=nama,
                alasan=f"Informasi penting dari keluarga lewat Eir: {sesi.tanda_bahaya}",
                waktu=berhenti,
                id_sesi=sesi.id_sesi,
            )
            for sesi, id_pasien, nama, berhenti in baris
        ]
