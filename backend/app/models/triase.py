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
    KATEGORI_KELUHAN,
    RISK_LEVEL,
    STATUS_VALIDASI,
    SUMBER_REKOMENDASI,
    SUMBER_TANDA_VITAL,
    TINGKAT_KESADARAN,
    JenisTriase,
    KategoriKeluhan,
    RiskLevel,
    StatusValidasi,
    SumberRekomendasi,
    SumberTandaVital,
    TingkatKesadaran,
)


class Triase(db.Model):
    """Penilaian awal atau ulang: keluhan, tanda vital, rekomendasi, dan status validasi."""

    __tablename__ = "triase"
    __table_args__ = (
        # Triase terakhir per kunjungan untuk daftar tunggu (Desain Bab 5).
        sa.Index("idx_triase_kunjungan", "id_kunjungan", sa.text("waktu_triase DESC")),
        sa.CheckConstraint("char_length(gejala) BETWEEN 10 AND 2000", name="ck_triase_gejala"),
        sa.CheckConstraint("skala_nyeri IS NULL OR skala_nyeri BETWEEN 0 AND 10", name="ck_triase_skala_nyeri"),
        # CHECK tanda vital diwajibkan SKPL Tabel 6.2. Rentangnya memakai nilai yang mungkin dicatat
        # (Desain Bab 5, sama dengan prototipe), bukan rentang wajar: nilai tidak wajar tetapi mungkin,
        # misalnya saturasi 85%, tetap diterima lalu ditandai sebagai peringatan (Desain 2.3).
        sa.CheckConstraint("td_sistolik BETWEEN 0 AND 320", name="ck_triase_td_sistolik"),
        sa.CheckConstraint("td_diastolik BETWEEN 0 AND 200", name="ck_triase_td_diastolik"),
        sa.CheckConstraint("nadi BETWEEN 0 AND 300", name="ck_triase_nadi"),
        sa.CheckConstraint("laju_napas BETWEEN 0 AND 80", name="ck_triase_laju_napas"),
        sa.CheckConstraint("suhu BETWEEN 20 AND 45", name="ck_triase_suhu"),
        sa.CheckConstraint("saturasi BETWEEN 0 AND 100", name="ck_saturasi"),
    )

    id_triase: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()"))
    id_kunjungan: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("kunjungan.id_kunjungan"))
    jenis: Mapped[JenisTriase] = mapped_column(JENIS_TRIASE)
    dibuat_oleh: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("pengguna.id_pengguna"))
    divalidasi_oleh: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("pengguna.id_pengguna"))
    keluhan_utama: Mapped[str] = mapped_column(sa.String(200))
    gejala: Mapped[str] = mapped_column(sa.Text)
    kategori_keluhan: Mapped[KategoriKeluhan | None] = mapped_column(KATEGORI_KELUHAN)
    skala_nyeri: Mapped[int | None] = mapped_column(sa.SmallInteger)
    tingkat_kesadaran: Mapped[TingkatKesadaran] = mapped_column(TINGKAT_KESADARAN)
    td_sistolik: Mapped[int] = mapped_column(sa.SmallInteger)
    td_diastolik: Mapped[int] = mapped_column(sa.SmallInteger)
    nadi: Mapped[int] = mapped_column(sa.SmallInteger)
    laju_napas: Mapped[int] = mapped_column(sa.SmallInteger)
    suhu: Mapped[Decimal] = mapped_column(sa.Numeric(3, 1))
    saturasi: Mapped[Decimal] = mapped_column(sa.Numeric(4, 1))
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
