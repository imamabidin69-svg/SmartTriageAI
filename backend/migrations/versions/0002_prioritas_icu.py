"""Perubahan lingkup ke prioritas pasien ICU.

- triase: kolom keluhan IGD (keluhan utama, gejala, kategori, skala nyeri) diganti oksigen tambahan, alat
  bantu (ventilator, vasopresor), lima hasil lab opsional, catatan, skor NEWS2, dan peluang perburukan.
- status_validasi: nilai baru "tercatat" untuk observasi yang levelnya tidak naik.
- kunjungan: nomor bed, asal ruangan, dan diagnosis masuk ICU; satu bed hanya untuk satu pasien aktif.
- konfigurasi: interval observasi Kritis, ambang NEWS2 7/5/3, interval 15/30/60/120 menit, versi model baru.

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

KATEGORI_KELUHAN = (
    "Penurunan kesadaran atau kejang",
    "Nyeri dada",
    "Sesak napas atau batuk",
    "Perdarahan",
    "Gangguan saraf",
    "Nyeri perut",
    "Demam",
    "Pusing",
    "Nyeri kepala",
    "Mual, muntah, atau diare",
    "Cedera atau luka",
    "Jantung berdebar",
    "Kulit atau alergi",
    "Mata, telinga, hidung, atau tenggorokan",
    "Nyeri punggung, pinggang, atau anggota gerak",
    "Lemas atau kelemahan umum",
    "Keluhan kemih atau kandungan",
    "Lainnya",
)
CHECK_LAB = {
    "ck_triase_laktat": "laktat BETWEEN 0 AND 30",
    "ck_triase_kreatinin": "kreatinin BETWEEN 0 AND 25",
    "ck_triase_trombosit": "trombosit BETWEEN 0 AND 2000",
    "ck_triase_leukosit": "leukosit BETWEEN 0 AND 300",
    "ck_triase_bilirubin": "bilirubin BETWEEN 0 AND 60",
    "ck_triase_skor_news2": "skor_news2 BETWEEN 0 AND 20",
    "ck_triase_peluang_perburukan": "peluang_perburukan BETWEEN 0 AND 1",
    "ck_triase_catatan": "char_length(catatan) <= 500",
}
STATUS_VALIDASI_LAMA = ("menunggu", "disetujui", "menunggu_review_dokter", "dikoreksi")


def upgrade():
    # ------------------------------------------------------------ triase
    op.drop_constraint("ck_triase_gejala", "triase", type_="check")
    op.drop_constraint("ck_triase_skala_nyeri", "triase", type_="check")
    for kolom in ("keluhan_utama", "gejala", "kategori_keluhan", "skala_nyeri"):
        op.drop_column("triase", kolom)
    op.execute("DROP TYPE IF EXISTS kategori_keluhan")

    for kolom in ("oksigen_tambahan", "ventilator", "vasopresor"):
        op.add_column("triase", sa.Column(kolom, sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column("triase", sa.Column("laktat", sa.Numeric(precision=3, scale=1), nullable=True))
    op.add_column("triase", sa.Column("kreatinin", sa.Numeric(precision=4, scale=2), nullable=True))
    op.add_column("triase", sa.Column("trombosit", sa.SmallInteger(), nullable=True))
    op.add_column("triase", sa.Column("leukosit", sa.Numeric(precision=4, scale=1), nullable=True))
    op.add_column("triase", sa.Column("bilirubin", sa.Numeric(precision=3, scale=1), nullable=True))
    op.add_column("triase", sa.Column("catatan", sa.Text(), nullable=True))
    # Baris lama (data IGD) diberi skor 0 lalu default dilepas, sehingga baris baru wajib mengisi skor.
    op.add_column("triase", sa.Column("skor_news2", sa.SmallInteger(), server_default="0", nullable=False))
    op.alter_column("triase", "skor_news2", server_default=None)
    op.add_column("triase", sa.Column("peluang_perburukan", sa.Numeric(precision=5, scale=4), nullable=True))
    for nama, syarat in CHECK_LAB.items():
        op.create_check_constraint(nama, "triase", syarat)

    # ADD VALUE boleh di dalam transaksi (PostgreSQL 12+) selama nilainya tidak dipakai di transaksi yang sama.
    op.execute("ALTER TYPE status_validasi ADD VALUE IF NOT EXISTS 'tercatat'")

    # ------------------------------------------------------------ kunjungan
    op.add_column("kunjungan", sa.Column("nomor_bed", sa.String(length=10), nullable=True))
    op.add_column("kunjungan", sa.Column("asal_ruangan", sa.String(length=60), nullable=True))
    op.add_column("kunjungan", sa.Column("diagnosis_masuk", sa.String(length=200), nullable=True))
    op.create_index(
        "uq_kunjungan_bed_aktif",
        "kunjungan",
        ["nomor_bed"],
        unique=True,
        postgresql_where=sa.text("status <> 'selesai' AND nomor_bed IS NOT NULL"),
    )

    # ------------------------------------------------------------ konfigurasi
    op.drop_constraint("ck_konfigurasi_batas_tunggu", "konfigurasi", type_="check")
    op.add_column(
        "konfigurasi", sa.Column("batas_tunggu_kritis", sa.SmallInteger(), server_default="15", nullable=False)
    )
    op.alter_column("konfigurasi", "batas_tunggu_kritis", server_default=None)
    op.execute(
        "UPDATE konfigurasi SET versi_model = 'rf-icu-physionet2019-v1', ambang_kritis = 7, ambang_tinggi = 5, "
        "ambang_sedang = 3, batas_tunggu_kritis = 15, batas_tunggu_tinggi = 30, batas_tunggu_sedang = 60, "
        "batas_tunggu_rendah = 120"
    )
    op.create_check_constraint(
        "ck_konfigurasi_batas_tunggu",
        "konfigurasi",
        "batas_tunggu_kritis > 0 AND batas_tunggu_kritis <= batas_tunggu_tinggi "
        "AND batas_tunggu_tinggi <= batas_tunggu_sedang AND batas_tunggu_sedang <= batas_tunggu_rendah",
    )


def downgrade():
    # ------------------------------------------------------------ konfigurasi
    op.drop_constraint("ck_konfigurasi_batas_tunggu", "konfigurasi", type_="check")
    op.drop_column("konfigurasi", "batas_tunggu_kritis")
    op.execute(
        "UPDATE konfigurasi SET versi_model = 'smarttriage-rf-v1.0.0', ambang_kritis = 6, ambang_tinggi = 4, "
        "ambang_sedang = 2, batas_tunggu_tinggi = 10, batas_tunggu_sedang = 30, batas_tunggu_rendah = 60"
    )
    op.create_check_constraint(
        "ck_konfigurasi_batas_tunggu",
        "konfigurasi",
        "batas_tunggu_tinggi > 0 AND batas_tunggu_tinggi <= batas_tunggu_sedang "
        "AND batas_tunggu_sedang <= batas_tunggu_rendah",
    )

    # ------------------------------------------------------------ kunjungan
    op.drop_index(
        "uq_kunjungan_bed_aktif",
        table_name="kunjungan",
        postgresql_where=sa.text("status <> 'selesai' AND nomor_bed IS NOT NULL"),
    )
    for kolom in ("diagnosis_masuk", "asal_ruangan", "nomor_bed"):
        op.drop_column("kunjungan", kolom)

    # ------------------------------------------------------------ status_validasi tanpa "tercatat"
    # PostgreSQL tidak bisa menghapus satu nilai ENUM, jadi tipenya dibuat ulang.
    op.execute("UPDATE triase SET status_validasi = 'disetujui' WHERE status_validasi = 'tercatat'")
    op.execute("ALTER TABLE triase ALTER COLUMN status_validasi DROP DEFAULT")
    op.execute("ALTER TYPE status_validasi RENAME TO status_validasi_lama")
    postgresql.ENUM(*STATUS_VALIDASI_LAMA, name="status_validasi").create(op.get_bind())
    op.execute(
        "ALTER TABLE triase ALTER COLUMN status_validasi TYPE status_validasi "
        "USING status_validasi::text::status_validasi"
    )
    op.execute("ALTER TABLE triase ALTER COLUMN status_validasi SET DEFAULT 'menunggu'")
    op.execute("DROP TYPE status_validasi_lama")

    # ------------------------------------------------------------ triase
    for nama in CHECK_LAB:
        op.drop_constraint(nama, "triase", type_="check")
    for kolom in (
        "peluang_perburukan",
        "skor_news2",
        "catatan",
        "bilirubin",
        "leukosit",
        "trombosit",
        "kreatinin",
        "laktat",
        "vasopresor",
        "ventilator",
        "oksigen_tambahan",
    ):
        op.drop_column("triase", kolom)

    # Kolom IGD dikembalikan; baris yang dibuat setelah 0002 diberi isian penanda karena datanya tidak ada.
    op.add_column(
        "triase", sa.Column("keluhan_utama", sa.String(length=200), server_default="Observasi ICU", nullable=False)
    )
    op.add_column("triase", sa.Column("gejala", sa.Text(), server_default="Observasi pasien ICU", nullable=False))
    op.alter_column("triase", "keluhan_utama", server_default=None)
    op.alter_column("triase", "gejala", server_default=None)
    postgresql.ENUM(*KATEGORI_KELUHAN, name="kategori_keluhan").create(op.get_bind())
    kategori = postgresql.ENUM(*KATEGORI_KELUHAN, name="kategori_keluhan", create_type=False)
    op.add_column("triase", sa.Column("kategori_keluhan", kategori, nullable=True))
    op.add_column("triase", sa.Column("skala_nyeri", sa.SmallInteger(), nullable=True))
    op.create_check_constraint("ck_triase_gejala", "triase", "char_length(gejala) BETWEEN 10 AND 2000")
    op.create_check_constraint("ck_triase_skala_nyeri", "triase", "skala_nyeri IS NULL OR skala_nyeri BETWEEN 0 AND 10")
