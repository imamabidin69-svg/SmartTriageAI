import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.enums import (
    JENIS_TRIASE,
    RISK_LEVEL,
    STATUS_VALIDASI,
    SUMBER_REKOMENDASI,
    SUMBER_TANDA_VITAL,
    TINGKAT_KESADARAN,
    JenisTriase,
    RiskLevel,
    StatusValidasi,
    SumberRekomendasi,
    SumberTandaVital,
    TingkatKesadaran,
)


class Triase(db.Model):
    """Satu observasi pasien ICU beserta penilaian prioritasnya (NEWS2 dan model) dan status validasi dokter.

    Nama tabel tetap "triase" dari SKPL; di ICU isinya adalah penilaian prioritas awal saat pasien masuk
    (jenis awal) dan setiap observasi berikutnya (jenis ulang).
    """

    __tablename__ = "triase"
    __table_args__ = (
        # Triase terakhir per kunjungan untuk daftar tunggu (Desain Bab 5).
        sa.Index("idx_triase_kunjungan", "id_kunjungan", sa.text("waktu_triase DESC")),
        sa.CheckConstraint("char_length(catatan) <= 500", name="ck_triase_catatan"),
        # CHECK tanda vital diwajibkan SKPL Tabel 6.2. Rentangnya memakai nilai yang mungkin dicatat
        # (Desain Bab 5, sama dengan prototipe), bukan rentang wajar: nilai tidak wajar tetapi mungkin,
        # misalnya saturasi 85%, tetap diterima lalu ditandai sebagai peringatan (Desain 2.3).
        sa.CheckConstraint("td_sistolik BETWEEN 0 AND 320", name="ck_triase_td_sistolik"),
        sa.CheckConstraint("td_diastolik BETWEEN 0 AND 200", name="ck_triase_td_diastolik"),
        sa.CheckConstraint("nadi BETWEEN 0 AND 300", name="ck_triase_nadi"),
        sa.CheckConstraint("laju_napas BETWEEN 0 AND 80", name="ck_triase_laju_napas"),
        sa.CheckConstraint("suhu BETWEEN 20 AND 45", name="ck_triase_suhu"),
        sa.CheckConstraint("saturasi BETWEEN 0 AND 100", name="ck_saturasi"),
        # Hasil laboratorium boleh kosong; rentang dibuat longgar untuk nilai yang mungkin dicatat.
        sa.CheckConstraint("laktat BETWEEN 0 AND 30", name="ck_triase_laktat"),
        sa.CheckConstraint("kreatinin BETWEEN 0 AND 25", name="ck_triase_kreatinin"),
        sa.CheckConstraint("trombosit BETWEEN 0 AND 2000", name="ck_triase_trombosit"),
        sa.CheckConstraint("leukosit BETWEEN 0 AND 300", name="ck_triase_leukosit"),
        sa.CheckConstraint("bilirubin BETWEEN 0 AND 60", name="ck_triase_bilirubin"),
        sa.CheckConstraint("skor_news2 BETWEEN 0 AND 20", name="ck_triase_skor_news2"),
        sa.CheckConstraint("peluang_perburukan BETWEEN 0 AND 1", name="ck_triase_peluang_perburukan"),
    )

    id_triase: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()"))
    id_kunjungan: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("kunjungan.id_kunjungan"))
    jenis: Mapped[JenisTriase] = mapped_column(JENIS_TRIASE)
    dibuat_oleh: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("pengguna.id_pengguna"))
    divalidasi_oleh: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("pengguna.id_pengguna"))
    tingkat_kesadaran: Mapped[TingkatKesadaran] = mapped_column(TINGKAT_KESADARAN)
    td_sistolik: Mapped[int] = mapped_column(sa.SmallInteger)
    td_diastolik: Mapped[int] = mapped_column(sa.SmallInteger)
    nadi: Mapped[int] = mapped_column(sa.SmallInteger)
    laju_napas: Mapped[int] = mapped_column(sa.SmallInteger)
    suhu: Mapped[Decimal] = mapped_column(sa.Numeric(3, 1))
    saturasi: Mapped[Decimal] = mapped_column(sa.Numeric(4, 1))
    oksigen_tambahan: Mapped[bool] = mapped_column(sa.Boolean, server_default=sa.false())
    ventilator: Mapped[bool] = mapped_column(sa.Boolean, server_default=sa.false())
    vasopresor: Mapped[bool] = mapped_column(sa.Boolean, server_default=sa.false())
    # Satuan: laktat mmol/L, kreatinin dan bilirubin mg/dL, trombosit dan leukosit ribu/µL.
    laktat: Mapped[Decimal | None] = mapped_column(sa.Numeric(3, 1))
    kreatinin: Mapped[Decimal | None] = mapped_column(sa.Numeric(4, 2))
    trombosit: Mapped[int | None] = mapped_column(sa.SmallInteger)
    leukosit: Mapped[Decimal | None] = mapped_column(sa.Numeric(4, 1))
    bilirubin: Mapped[Decimal | None] = mapped_column(sa.Numeric(3, 1))
    catatan: Mapped[str | None] = mapped_column(sa.Text)
    skor_news2: Mapped[int] = mapped_column(sa.SmallInteger)
    peluang_perburukan: Mapped[Decimal | None] = mapped_column(sa.Numeric(5, 4))
    sumber_tanda_vital: Mapped[SumberTandaVital] = mapped_column(SUMBER_TANDA_VITAL)
    risk_level: Mapped[RiskLevel] = mapped_column(RISK_LEVEL)
    sumber_rekomendasi: Mapped[SumberRekomendasi] = mapped_column(SUMBER_REKOMENDASI)
    penjelasan_ai: Mapped[dict[str, Any]] = mapped_column(JSONB)
    status_validasi: Mapped[StatusValidasi] = mapped_column(
        STATUS_VALIDASI, server_default=StatusValidasi.MENUNGGU.value
    )
    waktu_triase: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())

    kunjungan = relationship("Kunjungan", back_populates="triase")
    pembuat = relationship("Pengguna", foreign_keys=[dibuat_oleh])
    validator = relationship("Pengguna", foreign_keys=[divalidasi_oleh])
    pemindaian = relationship("PemindaianAlat", back_populates="triase")

    # ------------------------------------------------------------ perpindahan status validasi (FR-06)
    # Jalur yang sah (keputusan K2a): dari menunggu ke disetujui, dikoreksi, atau menunggu_review_dokter;
    # dari menunggu_review_dokter ke disetujui atau dikoreksi. Disetujui, dikoreksi, dan tercatat bersifat
    # final; tercatat dipakai untuk observasi yang levelnya tidak naik sehingga tidak perlu persetujuan dokter.
    # Hak peran diperiksa KebijakanValidasi; method ini hanya menjaga urutan status.

    STATUS_FINAL = (StatusValidasi.DISETUJUI, StatusValidasi.DIKOREKSI, StatusValidasi.TERCATAT)

    def bisa_diputuskan(self) -> bool:
        return self.status_validasi not in self.STATUS_FINAL

    def setujui(self, validator_id: uuid.UUID) -> None:
        self.status_validasi = StatusValidasi.DISETUJUI
        self.divalidasi_oleh = validator_id

    def koreksi(self, level: RiskLevel, validator_id: uuid.UUID) -> None:
        self.risk_level = level
        self.status_validasi = StatusValidasi.DIKOREKSI
        self.divalidasi_oleh = validator_id

    def ajukan_review(self) -> None:
        self.status_validasi = StatusValidasi.MENUNGGU_REVIEW_DOKTER
