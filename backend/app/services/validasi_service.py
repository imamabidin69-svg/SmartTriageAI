"""Validasi hasil triase oleh perawat atau dokter (FR-06, Desain 2.6 dan Gambar 2.16-2.18)."""

import uuid

from sqlalchemy import select

from app.extensions import db
from app.middleware.auth import AksesDitolakError
from app.models import Kunjungan, Pengguna, Triase
from app.models.enums import AksiAudit, Peran, RiskLevel, StatusKunjungan, StatusValidasi
from app.services.audit_logger import AuditLogger
from app.utils.errors import KonflikError, TidakDitemukanError, ValidasiGagalError
from app.utils.schemas import ValidasiRequest

AKSI_AUDIT = {
    "setujui": AksiAudit.SETUJUI,
    "koreksi": AksiAudit.KOREKSI,
    "ajukan_review": AksiAudit.AJUKAN_REVIEW,
}


class KebijakanValidasi:
    """Aturan peran di server: perawat hanya menyetujui hasil non-kritis atau mengajukan review,
    dokter menyetujui atau mengoreksi semua tingkat (Desain 2.6). Dokter tidak mengajukan review (K10).
    """

    @staticmethod
    def boleh(peran: Peran, aksi: str, level: RiskLevel) -> bool:
        if peran == Peran.PERAWAT:
            return aksi == "ajukan_review" or (aksi == "setujui" and level != RiskLevel.KRITIS)
        if peran == Peran.DOKTER:
            return aksi in ("setujui", "koreksi")
        return False

    @staticmethod
    def pesan_ditolak(peran: Peran, aksi: str) -> str:
        if peran == Peran.PERAWAT and aksi == "setujui":
            return "Hasil triase kritis harus divalidasi dokter. Ajukan review bila perlu."
        if peran == Peran.PERAWAT and aksi == "koreksi":
            return "Koreksi risk level hanya boleh dilakukan dokter. Ajukan review bila hasilnya meragukan."
        if peran == Peran.DOKTER and aksi == "ajukan_review":
            return "Dokter langsung menyetujui atau mengoreksi hasil triase, tanpa mengajukan review."
        return "Peran Anda tidak boleh memvalidasi hasil triase."


class ValidasiService:
    def __init__(self, kebijakan: KebijakanValidasi | None = None) -> None:
        self.kebijakan = kebijakan or KebijakanValidasi()

    def validasi(self, id_triase: uuid.UUID, data: ValidasiRequest, pengguna: Pengguna) -> Triase:
        try:
            triase = self._validasi(id_triase, data, pengguna)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        db.session.refresh(triase)
        return triase

    def _validasi(self, id_triase: uuid.UUID, data: ValidasiRequest, pengguna: Pengguna) -> Triase:
        # Baris dikunci lalu dibaca ulang dari basis data, supaya status yang diperiksa bukan salinan lama.
        triase = db.session.scalar(
            select(Triase)
            .where(Triase.id_triase == id_triase)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if triase is None:
            raise TidakDitemukanError("Triase tidak ditemukan.")
        if not self.kebijakan.boleh(pengguna.peran, data.aksi, triase.risk_level):
            raise AksesDitolakError(self.kebijakan.pesan_ditolak(pengguna.peran, data.aksi))
        self._periksa_status(triase, data.aksi, pengguna)

        sebelum = triase.risk_level
        if data.aksi == "setujui":
            triase.setujui(pengguna.id_pengguna)
        elif data.aksi == "koreksi":
            if data.risk_level == sebelum:
                raise ValidasiGagalError(
                    [{"field": "risk_level", "pesan": f"Level koreksi sama dengan level saat ini ({sebelum.value})."}]
                )
            triase.koreksi(data.risk_level, pengguna.id_pengguna)
        else:
            triase.ajukan_review()

        AuditLogger().catat(
            AKSI_AUDIT[data.aksi],
            pengguna,
            id_triase=triase.id_triase,
            sebelum=sebelum,
            sesudah=triase.risk_level,
            catatan=data.alasan,
        )
        return triase

    @staticmethod
    def _periksa_status(triase: Triase, aksi: str, pengguna: Pengguna) -> None:
        if not triase.bisa_diputuskan():
            raise KonflikError(f"Triase ini sudah divalidasi ({triase.status_validasi.value}).")
        if triase.status_validasi == StatusValidasi.MENUNGGU_REVIEW_DOKTER and pengguna.peran != Peran.DOKTER:
            raise KonflikError("Triase ini sedang menunggu review dokter.")

        # Kunjungan dikunci FOR SHARE supaya triase ulang (yang mengunci kunjungan FOR UPDATE) tidak bisa
        # tersimpan di antara pemeriksaan "triase terakhir" ini dan commit.
        status_kunjungan = db.session.scalar(
            select(Kunjungan.status).where(Kunjungan.id_kunjungan == triase.id_kunjungan).with_for_update(read=True)
        )
        if status_kunjungan == StatusKunjungan.SELESAI:
            raise KonflikError("Kunjungan ini sudah selesai, jadi triasenya tidak bisa divalidasi lagi.")

        terbaru = db.session.scalar(
            select(Triase.id_triase)
            .where(Triase.id_kunjungan == triase.id_kunjungan)
            .order_by(Triase.waktu_triase.desc(), Triase.id_triase.desc())
            .limit(1)
        )
        if terbaru != triase.id_triase:
            raise KonflikError("Triase ini sudah digantikan triase ulang yang lebih baru.")
