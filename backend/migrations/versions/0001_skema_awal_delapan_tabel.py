"""Skema awal delapan tabel sesuai PDM SKPL v3.0 dan ERD Desain Arsitektur Backend v2.0.

Selain tabel hasil autogenerate, migrasi ini menyisipkan baris konfigurasi bawaan dan mengatur
hak akses role aplikasi smarttriage_app: log_audit hanya boleh dibaca dan ditambah (NFR-06).

Revision ID: 0001
Revises:
Create Date: 2026-10-09 17:51:24.325802

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# Penanda revisi untuk Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

ROLE_APLIKASI = "smarttriage_app"

TIPE_ENUM = (
    "peran",
    "jenis_kelamin",
    "status_kunjungan",
    "jenis_triase",
    "kategori_keluhan",
    "tingkat_kesadaran",
    "sumber_tanda_vital",
    "risk_level",
    "sumber_rekomendasi",
    "status_validasi",
    "jenis_alat",
    "pengisi_eir",
    "status_sesi_eir",
    "aksi_audit",
)

# Hak akses role aplikasi. Migrasi gagal bila role belum dibuat, supaya aplikasi tidak diam-diam
# berjalan sebagai pemilik tabel yang bisa mengubah log_audit. TRUNCATE tidak pernah diberikan.
SQL_HAK_AKSES = f"""
DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_roles WHERE rolname = '{ROLE_APLIKASI}') THEN
    GRANT USAGE ON SCHEMA public TO {ROLE_APLIKASI};
    GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {ROLE_APLIKASI};
    GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {ROLE_APLIKASI};
    -- Log audit append-only (Desain Bab 5, NFR-06).
    REVOKE UPDATE, DELETE ON log_audit FROM {ROLE_APLIKASI};
    REVOKE ALL ON alembic_version FROM {ROLE_APLIKASI};
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {ROLE_APLIKASI};
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO {ROLE_APLIKASI};
  ELSE
    RAISE EXCEPTION 'Role % belum ada. Buat role ini sebelum menjalankan flask db upgrade.', '{ROLE_APLIKASI}';
  END IF;
END
$$;
"""

SQL_CABUT_HAK_AKSES = f"""
DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_roles WHERE rolname = '{ROLE_APLIKASI}') THEN
    ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLES FROM {ROLE_APLIKASI};
    ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE USAGE, SELECT ON SEQUENCES FROM {ROLE_APLIKASI};
  END IF;
END
$$;
"""


def upgrade():
    # Bagian berikut dibangkitkan Alembic dari model, lalu diperiksa manual.
    op.create_table(
        "konfigurasi",
        sa.Column("id_konfigurasi", sa.SmallInteger(), autoincrement=False, nullable=False),
        sa.Column("versi_model", sa.String(length=50), nullable=False),
        sa.Column("ambang_kritis", sa.SmallInteger(), nullable=False),
        sa.Column("ambang_tinggi", sa.SmallInteger(), nullable=False),
        sa.Column("ambang_sedang", sa.SmallInteger(), nullable=False),
        sa.Column("batas_tunggu_tinggi", sa.SmallInteger(), nullable=False),
        sa.Column("batas_tunggu_sedang", sa.SmallInteger(), nullable=False),
        sa.Column("batas_tunggu_rendah", sa.SmallInteger(), nullable=False),
        sa.Column("ambang_keyakinan", sa.Numeric(precision=3, scale=2), nullable=False),
        sa.CheckConstraint(
            "ambang_keyakinan BETWEEN 0 AND 1",
            name=op.f("ck_konfigurasi_ambang_keyakinan"),
        ),
        sa.CheckConstraint(
            "ambang_kritis > ambang_tinggi AND ambang_tinggi > ambang_sedang AND ambang_sedang > 0",
            name=op.f("ck_konfigurasi_ambang_berurutan"),
        ),
        sa.CheckConstraint(
            "batas_tunggu_tinggi > 0 AND batas_tunggu_tinggi <= batas_tunggu_sedang "
            "AND batas_tunggu_sedang <= batas_tunggu_rendah",
            name=op.f("ck_konfigurasi_batas_tunggu"),
        ),
        sa.CheckConstraint("id_konfigurasi = 1", name=op.f("ck_konfigurasi_satu_baris")),
        sa.PrimaryKeyConstraint("id_konfigurasi", name=op.f("pk_konfigurasi")),
    )
    op.create_table(
        "pengguna",
        sa.Column(
            "id_pengguna",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("nama", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=150), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("peran", sa.Enum("perawat", "dokter", "admin", name="peran"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("email = lower(email)", name=op.f("ck_pengguna_email_huruf_kecil")),
        sa.PrimaryKeyConstraint("id_pengguna", name=op.f("pk_pengguna")),
        sa.UniqueConstraint("email", name=op.f("uq_pengguna_email")),
    )
    op.create_table(
        "pasien",
        sa.Column(
            "id_pasien",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("didaftarkan_oleh", sa.Uuid(), nullable=False),
        sa.Column("nama", sa.String(length=120), nullable=False),
        sa.Column("tanggal_lahir", sa.Date(), nullable=True),
        sa.Column("perkiraan_usia", sa.SmallInteger(), nullable=True),
        sa.Column(
            "jenis_kelamin",
            sa.Enum("laki_laki", "perempuan", name="jenis_kelamin"),
            nullable=False,
        ),
        sa.Column("nik", sa.CHAR(length=16), nullable=True),
        sa.Column("no_telepon", sa.String(length=20), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("nik IS NULL OR nik ~ '^[0-9]{16}$'", name=op.f("ck_pasien_nik_format")),
        sa.CheckConstraint(
            "perkiraan_usia IS NULL OR perkiraan_usia BETWEEN 0 AND 150",
            name=op.f("ck_pasien_perkiraan_usia"),
        ),
        sa.CheckConstraint(
            "tanggal_lahir IS NOT NULL OR perkiraan_usia IS NOT NULL",
            name=op.f("ck_pasien_tanggal_lahir_atau_usia"),
        ),
        sa.ForeignKeyConstraint(
            ["didaftarkan_oleh"],
            ["pengguna.id_pengguna"],
            name=op.f("fk_pasien_didaftarkan_oleh_pengguna"),
        ),
        sa.PrimaryKeyConstraint("id_pasien", name=op.f("pk_pasien")),
    )
    op.create_index(
        "uq_pasien_nik",
        "pasien",
        ["nik"],
        unique=True,
        postgresql_where=sa.text("nik IS NOT NULL"),
    )
    op.create_table(
        "kunjungan",
        sa.Column(
            "id_kunjungan",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("id_pasien", sa.Uuid(), nullable=False),
        sa.Column(
            "waktu_datang",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("waktu_ditangani", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.Enum("menunggu", "ditangani", "selesai", name="status_kunjungan"),
            server_default="menunggu",
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["id_pasien"],
            ["pasien.id_pasien"],
            name=op.f("fk_kunjungan_id_pasien_pasien"),
        ),
        sa.PrimaryKeyConstraint("id_kunjungan", name=op.f("pk_kunjungan")),
    )
    op.create_index(
        "idx_kunjungan_pasien",
        "kunjungan",
        ["id_pasien", sa.literal_column("waktu_datang DESC")],
        unique=False,
    )
    op.create_index("idx_kunjungan_status", "kunjungan", ["status", "waktu_datang"], unique=False)
    op.create_table(
        "sesi_eir",
        sa.Column(
            "id_sesi",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("id_kunjungan", sa.Uuid(), nullable=False),
        sa.Column("pengisi", sa.Enum("pasien", "keluarga", name="pengisi_eir"), nullable=False),
        sa.Column("waktu_persetujuan", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            sa.Enum("berjalan", "selesai", "dihentikan", name="status_sesi_eir"),
            server_default="berjalan",
            nullable=False,
        ),
        sa.Column("tanda_bahaya", sa.Text(), nullable=True),
        sa.Column(
            "transkrip",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("ringkasan", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("waktu_selesai", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["id_kunjungan"],
            ["kunjungan.id_kunjungan"],
            name=op.f("fk_sesi_eir_id_kunjungan_kunjungan"),
        ),
        sa.PrimaryKeyConstraint("id_sesi", name=op.f("pk_sesi_eir")),
    )
    op.create_table(
        "triase",
        sa.Column(
            "id_triase",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("id_kunjungan", sa.Uuid(), nullable=False),
        sa.Column("jenis", sa.Enum("awal", "ulang", name="jenis_triase"), nullable=False),
        sa.Column("dibuat_oleh", sa.Uuid(), nullable=False),
        sa.Column("divalidasi_oleh", sa.Uuid(), nullable=True),
        sa.Column("keluhan_utama", sa.String(length=200), nullable=False),
        sa.Column("gejala", sa.Text(), nullable=False),
        sa.Column(
            "kategori_keluhan",
            sa.Enum(
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
                name="kategori_keluhan",
            ),
            nullable=True,
        ),
        sa.Column("skala_nyeri", sa.SmallInteger(), nullable=True),
        sa.Column(
            "tingkat_kesadaran",
            sa.Enum("A", "V", "P", "U", name="tingkat_kesadaran"),
            nullable=False,
        ),
        sa.Column("td_sistolik", sa.SmallInteger(), nullable=False),
        sa.Column("td_diastolik", sa.SmallInteger(), nullable=False),
        sa.Column("nadi", sa.SmallInteger(), nullable=False),
        sa.Column("laju_napas", sa.SmallInteger(), nullable=False),
        sa.Column("suhu", sa.Numeric(precision=3, scale=1), nullable=False),
        sa.Column("saturasi", sa.Numeric(precision=4, scale=1), nullable=False),
        sa.Column(
            "sumber_tanda_vital",
            sa.Enum("manual", "pemindaian", "campuran", name="sumber_tanda_vital"),
            nullable=False,
        ),
        sa.Column(
            "risk_level",
            sa.Enum("rendah", "sedang", "tinggi", "kritis", name="risk_level"),
            nullable=False,
        ),
        sa.Column(
            "sumber_rekomendasi",
            sa.Enum("model", "aturan", name="sumber_rekomendasi"),
            nullable=False,
        ),
        sa.Column("penjelasan_ai", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "status_validasi",
            sa.Enum(
                "menunggu",
                "disetujui",
                "menunggu_review_dokter",
                "dikoreksi",
                name="status_validasi",
            ),
            server_default="menunggu",
            nullable=False,
        ),
        sa.Column(
            "waktu_triase",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("char_length(gejala) BETWEEN 10 AND 2000", name=op.f("ck_triase_gejala")),
        sa.CheckConstraint("laju_napas BETWEEN 0 AND 80", name=op.f("ck_triase_laju_napas")),
        sa.CheckConstraint("nadi BETWEEN 0 AND 300", name=op.f("ck_triase_nadi")),
        sa.CheckConstraint("saturasi BETWEEN 0 AND 100", name=op.f("ck_saturasi")),
        sa.CheckConstraint(
            "skala_nyeri IS NULL OR skala_nyeri BETWEEN 0 AND 10",
            name=op.f("ck_triase_skala_nyeri"),
        ),
        sa.CheckConstraint("suhu BETWEEN 20 AND 45", name=op.f("ck_triase_suhu")),
        sa.CheckConstraint("td_diastolik BETWEEN 0 AND 200", name=op.f("ck_triase_td_diastolik")),
        sa.CheckConstraint("td_sistolik BETWEEN 0 AND 320", name=op.f("ck_triase_td_sistolik")),
        sa.ForeignKeyConstraint(
            ["dibuat_oleh"],
            ["pengguna.id_pengguna"],
            name=op.f("fk_triase_dibuat_oleh_pengguna"),
        ),
        sa.ForeignKeyConstraint(
            ["divalidasi_oleh"],
            ["pengguna.id_pengguna"],
            name=op.f("fk_triase_divalidasi_oleh_pengguna"),
        ),
        sa.ForeignKeyConstraint(
            ["id_kunjungan"],
            ["kunjungan.id_kunjungan"],
            name=op.f("fk_triase_id_kunjungan_kunjungan"),
        ),
        sa.PrimaryKeyConstraint("id_triase", name=op.f("pk_triase")),
    )
    op.create_index(
        "idx_triase_kunjungan",
        "triase",
        ["id_kunjungan", sa.literal_column("waktu_triase DESC")],
        unique=False,
    )
    op.create_table(
        "log_audit",
        sa.Column(
            "id_log",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("id_aktor", sa.Uuid(), nullable=False),
        sa.Column("id_triase", sa.Uuid(), nullable=True),
        sa.Column(
            "aksi",
            sa.Enum(
                "setujui",
                "koreksi",
                "ajukan_review",
                "ubah_konfigurasi",
                "tambah_staf",
                "ubah_staf",
                "nonaktifkan_staf",
                "aktifkan_staf",
                "atur_ulang_password",
                "registrasi_kunjungan",
                name="aksi_audit",
            ),
            nullable=False,
        ),
        sa.Column("catatan", sa.Text(), nullable=True),
        sa.Column(
            "level_sebelum",
            sa.Enum("rendah", "sedang", "tinggi", "kritis", name="risk_level"),
            nullable=True,
        ),
        sa.Column(
            "level_sesudah",
            sa.Enum("rendah", "sedang", "tinggi", "kritis", name="risk_level"),
            nullable=True,
        ),
        sa.Column(
            "waktu",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "aksi NOT IN ('koreksi', 'ajukan_review') OR coalesce(char_length(btrim(catatan)), 0) >= 5",
            name=op.f("ck_alasan"),
        ),
        sa.ForeignKeyConstraint(
            ["id_aktor"],
            ["pengguna.id_pengguna"],
            name=op.f("fk_log_audit_id_aktor_pengguna"),
        ),
        sa.ForeignKeyConstraint(
            ["id_triase"],
            ["triase.id_triase"],
            name=op.f("fk_log_audit_id_triase_triase"),
        ),
        sa.PrimaryKeyConstraint("id_log", name=op.f("pk_log_audit")),
    )
    op.create_table(
        "pemindaian_alat",
        sa.Column(
            "id_pemindaian",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("id_triase", sa.Uuid(), nullable=True),
        sa.Column("dipindai_oleh", sa.Uuid(), nullable=False),
        sa.Column(
            "jenis_alat",
            sa.Enum(
                "tensimeter",
                "oksimeter",
                "termometer",
                "bedside_monitor",
                name="jenis_alat",
            ),
            nullable=False,
        ),
        sa.Column("nilai_terbaca", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("nilai_dikonfirmasi", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("keyakinan", sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column(
            "waktu",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("keyakinan BETWEEN 0 AND 1", name=op.f("ck_pemindaian_alat_keyakinan")),
        sa.ForeignKeyConstraint(
            ["dipindai_oleh"],
            ["pengguna.id_pengguna"],
            name=op.f("fk_pemindaian_alat_dipindai_oleh_pengguna"),
        ),
        sa.ForeignKeyConstraint(
            ["id_triase"],
            ["triase.id_triase"],
            name=op.f("fk_pemindaian_alat_id_triase_triase"),
        ),
        sa.PrimaryKeyConstraint("id_pemindaian", name=op.f("pk_pemindaian_alat")),
    )

    # Baris konfigurasi bawaan: ambang aturan cadangan dari prototipe (ai-config-store.ts),
    # batas tunggu 10/30/60 menit (Desain 2.7), dan ambang keyakinan pemindaian 0,85 (Desain 2.4).
    tabel_konfigurasi = sa.table(
        "konfigurasi",
        sa.column("id_konfigurasi", sa.SmallInteger),
        sa.column("versi_model", sa.String),
        sa.column("ambang_kritis", sa.SmallInteger),
        sa.column("ambang_tinggi", sa.SmallInteger),
        sa.column("ambang_sedang", sa.SmallInteger),
        sa.column("batas_tunggu_tinggi", sa.SmallInteger),
        sa.column("batas_tunggu_sedang", sa.SmallInteger),
        sa.column("batas_tunggu_rendah", sa.SmallInteger),
        sa.column("ambang_keyakinan", sa.Numeric(3, 2)),
    )
    op.bulk_insert(
        tabel_konfigurasi,
        [
            {
                "id_konfigurasi": 1,
                "versi_model": "smarttriage-rf-v1.0.0",
                "ambang_kritis": 6,
                "ambang_tinggi": 4,
                "ambang_sedang": 2,
                "batas_tunggu_tinggi": 10,
                "batas_tunggu_sedang": 30,
                "batas_tunggu_rendah": 60,
                "ambang_keyakinan": 0.85,
            }
        ],
    )

    op.execute(SQL_HAK_AKSES)


def downgrade():
    op.execute(SQL_CABUT_HAK_AKSES)

    # Bagian berikut dibangkitkan Alembic dari model, lalu diperiksa manual.
    op.drop_table("pemindaian_alat")
    op.drop_table("log_audit")
    op.drop_index("idx_triase_kunjungan", table_name="triase")
    op.drop_table("triase")
    op.drop_table("sesi_eir")
    op.drop_index("idx_kunjungan_status", table_name="kunjungan")
    op.drop_index("idx_kunjungan_pasien", table_name="kunjungan")
    op.drop_table("kunjungan")
    op.drop_index(
        "uq_pasien_nik",
        table_name="pasien",
        postgresql_where=sa.text("nik IS NOT NULL"),
    )
    op.drop_table("pasien")
    op.drop_table("pengguna")
    op.drop_table("konfigurasi")

    # Alembic tidak menghapus tipe ENUM saat tabel dihapus, jadi dihapus manual di sini.
    for nama in TIPE_ENUM:
        op.execute(f"DROP TYPE IF EXISTS {nama}")
