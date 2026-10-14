"""POST /triase/{id}/validasi dan log auditnya (FR-06, NFR-06, Desain Gambar 2.16-2.18, keputusan K2a)."""

import uuid
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.models import LogAudit
from app.models.enums import AksiAudit, Peran, RiskLevel, StatusKunjungan, StatusValidasi
from app.services.audit_logger import AuditLogger
from app.services.validasi_service import KebijakanValidasi
from app.utils.errors import Tipe
from app.utils.waktu import sekarang


def _url(triase) -> str:
    return f"/api/v1/triase/{triase.id_triase}/validasi"


def _log(sesi_db, triase):
    return sesi_db.scalars(select(LogAudit).where(LogAudit.id_triase == triase.id_triase)).all()


@pytest.fixture
def perawat(masuk):
    return masuk(Peran.PERAWAT)


@pytest.fixture
def dokter(masuk):
    return masuk(Peran.DOKTER)


@pytest.fixture
def triase_sedang(kunjungan, buat_triase):
    return buat_triase(kunjungan, RiskLevel.SEDANG)


@pytest.fixture
def triase_kritis(kunjungan, buat_triase):
    return buat_triase(kunjungan, RiskLevel.KRITIS)


# ---------------------------------------------------------------- jalur berhasil


def test_perawat_menyetujui_hasil_non_kritis(client, perawat, triase_sedang, sesi_db):
    pengguna, header = perawat
    respons = client.post(_url(triase_sedang), json={"aksi": "setujui"}, headers=header)

    assert respons.status_code == 200
    isi = respons.get_json()
    assert isi["id_triase"] == str(triase_sedang.id_triase)
    assert isi["status_validasi"] == "disetujui"
    assert isi["risk_level"] == "sedang"
    assert isi["divalidasi_oleh"] == {"id_pengguna": str(pengguna.id_pengguna), "nama": pengguna.nama}

    [log] = _log(sesi_db, triase_sedang)
    assert log.aksi == AksiAudit.SETUJUI
    assert log.id_aktor == pengguna.id_pengguna
    assert (log.level_sebelum, log.level_sesudah) == (RiskLevel.SEDANG, RiskLevel.SEDANG)
    assert log.catatan is None


def test_alasan_saat_menyetujui_boleh_diisi_dan_disimpan(client, perawat, triase_sedang, sesi_db):
    _, header = perawat
    respons = client.post(_url(triase_sedang), json={"aksi": "setujui", "alasan": "  Sesuai kondisi  "}, headers=header)
    assert respons.status_code == 200
    assert _log(sesi_db, triase_sedang)[0].catatan == "Sesuai kondisi"


def test_alasan_kosong_saat_menyetujui_dianggap_tidak_diisi(client, perawat, triase_sedang, sesi_db):
    _, header = perawat
    assert client.post(_url(triase_sedang), json={"aksi": "setujui", "alasan": "  "}, headers=header).status_code == 200
    assert _log(sesi_db, triase_sedang)[0].catatan is None


@pytest.mark.parametrize("level", [RiskLevel.RENDAH, RiskLevel.KRITIS])
def test_perawat_mengajukan_review_semua_level(client, perawat, kunjungan, buat_triase, sesi_db, level):
    triase = buat_triase(kunjungan, level)
    _, header = perawat
    respons = client.post(_url(triase), json={"aksi": "ajukan_review", "alasan": "Nadi tidak stabil"}, headers=header)

    assert respons.status_code == 200
    isi = respons.get_json()
    assert isi["status_validasi"] == "menunggu_review_dokter"
    # divalidasi_oleh hanya diisi saat setujui dan koreksi.
    assert isi["divalidasi_oleh"] is None
    assert isi["catatan_validasi_terakhir"] == "Nadi tidak stabil"
    [log] = _log(sesi_db, triase)
    assert (log.aksi, log.catatan) == (AksiAudit.AJUKAN_REVIEW, "Nadi tidak stabil")
    assert (log.level_sebelum, log.level_sesudah) == (level, level)


def test_dokter_mengoreksi_risk_level(client, dokter, triase_sedang, sesi_db):
    pengguna, header = dokter
    isian = {"aksi": "koreksi", "risk_level": "tinggi", "alasan": "Nyeri dada khas"}
    respons = client.post(_url(triase_sedang), json=isian, headers=header)

    assert respons.status_code == 200
    isi = respons.get_json()
    assert isi["status_validasi"] == "dikoreksi"
    assert isi["risk_level"] == "tinggi"
    assert isi["divalidasi_oleh"]["id_pengguna"] == str(pengguna.id_pengguna)
    assert isi["catatan_validasi_terakhir"] == "Nyeri dada khas"
    [log] = _log(sesi_db, triase_sedang)
    assert log.aksi == AksiAudit.KOREKSI
    assert (log.level_sebelum, log.level_sesudah) == (RiskLevel.SEDANG, RiskLevel.TINGGI)


def test_dokter_menyetujui_hasil_kritis(client, dokter, triase_kritis):
    _, header = dokter
    respons = client.post(_url(triase_kritis), json={"aksi": "setujui"}, headers=header)
    assert respons.status_code == 200
    assert respons.get_json()["status_validasi"] == "disetujui"


@pytest.mark.parametrize(
    ("isian", "status"),
    [
        ({"aksi": "setujui"}, "disetujui"),
        ({"aksi": "koreksi", "risk_level": "rendah", "alasan": "Keluhan sudah membaik"}, "dikoreksi"),
    ],
)
def test_dokter_memutuskan_ajuan_review(client, dokter, kunjungan, buat_triase, isian, status):
    triase = buat_triase(kunjungan, RiskLevel.SEDANG, StatusValidasi.MENUNGGU_REVIEW_DOKTER)
    _, header = dokter
    respons = client.post(_url(triase), json=isian, headers=header)
    assert respons.status_code == 200
    assert respons.get_json()["status_validasi"] == status


def test_validasi_boleh_saat_pasien_sedang_ditangani(client, dokter, buat_kunjungan, buat_triase):
    triase = buat_triase(buat_kunjungan(status=StatusKunjungan.DITANGANI), RiskLevel.TINGGI)
    _, header = dokter
    assert client.post(_url(triase), json={"aksi": "setujui"}, headers=header).status_code == 200


# ---------------------------------------------------------------- aturan peran (403)


@pytest.mark.parametrize(
    ("peran", "isian", "level", "pesan"),
    [
        (
            Peran.PERAWAT,
            {"aksi": "setujui"},
            RiskLevel.KRITIS,
            "Hasil triase kritis harus divalidasi dokter. Ajukan review bila perlu.",
        ),
        (
            Peran.PERAWAT,
            {"aksi": "koreksi", "risk_level": "tinggi", "alasan": "Tampak sesak"},
            RiskLevel.SEDANG,
            "Koreksi risk level hanya boleh dilakukan dokter. Ajukan review bila hasilnya meragukan.",
        ),
        (
            Peran.DOKTER,
            {"aksi": "ajukan_review", "alasan": "Perlu konsultasi"},
            RiskLevel.SEDANG,
            "Dokter langsung menyetujui atau mengoreksi hasil triase, tanpa mengajukan review.",
        ),
    ],
)
def test_aksi_di_luar_hak_peran_ditolak(client, masuk, kunjungan, buat_triase, sesi_db, peran, isian, level, pesan):
    triase = buat_triase(kunjungan, level)
    _, header = masuk(peran)
    respons = client.post(_url(triase), json=isian, headers=header)

    assert respons.status_code == 403
    assert respons.get_json()["type"] == Tipe.AKSES_DITOLAK
    assert respons.get_json()["detail"] == pesan
    sesi_db.refresh(triase)
    assert triase.status_validasi == StatusValidasi.MENUNGGU
    assert _log(sesi_db, triase) == []


def test_admin_tidak_boleh_memvalidasi(client, masuk, triase_sedang):
    _, header = masuk(Peran.ADMIN)
    assert client.post(_url(triase_sedang), json={"aksi": "setujui"}, headers=header).status_code == 403


def test_validasi_tanpa_login_ditolak(client, triase_sedang):
    assert client.post(_url(triase_sedang), json={"aksi": "setujui"}).status_code == 401


@pytest.mark.parametrize(
    ("peran", "aksi", "level", "boleh"),
    [
        (peran, aksi, level, boleh)
        for level in RiskLevel
        for peran, aksi, boleh in [
            (Peran.PERAWAT, "setujui", level != RiskLevel.KRITIS),
            (Peran.PERAWAT, "koreksi", False),
            (Peran.PERAWAT, "ajukan_review", True),
            (Peran.DOKTER, "setujui", True),
            (Peran.DOKTER, "koreksi", True),
            (Peran.DOKTER, "ajukan_review", False),
            (Peran.ADMIN, "setujui", False),
            (Peran.ADMIN, "koreksi", False),
            (Peran.ADMIN, "ajukan_review", False),
        ]
    ],
)
def test_tabel_kebijakan_validasi(peran, aksi, level, boleh):
    assert KebijakanValidasi.boleh(peran, aksi, level) is boleh


def test_pesan_penolakan_bawaan():
    assert KebijakanValidasi.pesan_ditolak(Peran.ADMIN, "setujui") == "Peran Anda tidak boleh memvalidasi hasil triase."


# ---------------------------------------------------------------- status sudah berubah (409)


@pytest.mark.parametrize("status", [StatusValidasi.DISETUJUI, StatusValidasi.DIKOREKSI])
@pytest.mark.parametrize(
    "isian",
    [{"aksi": "setujui"}, {"aksi": "koreksi", "risk_level": "kritis", "alasan": "Kondisi memburuk"}],
)
def test_triase_final_tidak_bisa_divalidasi_lagi(client, dokter, kunjungan, buat_triase, sesi_db, status, isian):
    triase = buat_triase(kunjungan, RiskLevel.TINGGI, status)
    _, header = dokter
    respons = client.post(_url(triase), json=isian, headers=header)

    assert respons.status_code == 409
    assert respons.get_json()["type"] == Tipe.KONFLIK
    assert respons.get_json()["detail"] == f"Triase ini sudah divalidasi ({status.value})."
    assert _log(sesi_db, triase) == []


@pytest.mark.parametrize("isian", [{"aksi": "setujui"}, {"aksi": "ajukan_review", "alasan": "Mohon dicek ulang"}])
def test_ajuan_review_hanya_diputuskan_dokter(client, perawat, kunjungan, buat_triase, isian):
    triase = buat_triase(kunjungan, RiskLevel.SEDANG, StatusValidasi.MENUNGGU_REVIEW_DOKTER)
    _, header = perawat
    respons = client.post(_url(triase), json=isian, headers=header)
    assert respons.status_code == 409
    assert respons.get_json()["detail"] == "Triase ini sedang menunggu review dokter."


def test_triase_lama_tidak_bisa_divalidasi(client, dokter, kunjungan, buat_triase):
    waktu = sekarang()
    lama = buat_triase(kunjungan, RiskLevel.SEDANG, waktu=waktu - timedelta(minutes=40))
    buat_triase(kunjungan, RiskLevel.TINGGI, waktu=waktu - timedelta(minutes=5))
    _, header = dokter
    respons = client.post(_url(lama), json={"aksi": "setujui"}, headers=header)
    assert respons.status_code == 409
    assert respons.get_json()["detail"] == "Triase ini sudah digantikan triase ulang yang lebih baru."


def test_kunjungan_selesai_tidak_bisa_divalidasi(client, dokter, buat_kunjungan, buat_triase):
    triase = buat_triase(buat_kunjungan(status=StatusKunjungan.SELESAI), RiskLevel.SEDANG)
    _, header = dokter
    respons = client.post(_url(triase), json={"aksi": "setujui"}, headers=header)
    assert respons.status_code == 409
    assert respons.get_json()["detail"] == "Kunjungan ini sudah selesai, jadi triasenya tidak bisa divalidasi lagi."


def test_triase_tidak_ada(client, dokter):
    _, header = dokter
    respons = client.post(f"/api/v1/triase/{uuid.uuid4()}/validasi", json={"aksi": "setujui"}, headers=header)
    assert respons.status_code == 404
    assert respons.get_json()["detail"] == "Triase tidak ditemukan."


# ---------------------------------------------------------------- isian tidak valid (422)


def test_koreksi_ke_level_yang_sama_ditolak(client, dokter, triase_sedang, sesi_db):
    _, header = dokter
    isian = {"aksi": "koreksi", "risk_level": "sedang", "alasan": "Tetap sedang"}
    respons = client.post(_url(triase_sedang), json=isian, headers=header)
    assert respons.status_code == 422
    assert respons.get_json()["errors"] == [
        {"field": "risk_level", "pesan": "Level koreksi sama dengan level saat ini (sedang)."}
    ]
    assert _log(sesi_db, triase_sedang) == []


@pytest.mark.parametrize(
    ("isian", "errors"),
    [
        (
            {"aksi": "koreksi", "risk_level": "tinggi", "alasan": "abcd"},
            [{"field": "alasan", "pesan": "Alasan koreksi wajib diisi minimal 5 karakter."}],
        ),
        (
            {"aksi": "koreksi", "risk_level": "tinggi"},
            [{"field": "alasan", "pesan": "Alasan koreksi wajib diisi minimal 5 karakter."}],
        ),
        (
            # Spasi di awal dan akhir tidak dihitung.
            {"aksi": "ajukan_review", "alasan": "  ab   "},
            [{"field": "alasan", "pesan": "Alasan ajuan review wajib diisi minimal 5 karakter."}],
        ),
        (
            {"aksi": "ajukan_review", "alasan": ""},
            [{"field": "alasan", "pesan": "Alasan ajuan review wajib diisi minimal 5 karakter."}],
        ),
        (
            {"aksi": "koreksi", "alasan": "Kondisi memburuk"},
            [{"field": "risk_level", "pesan": "Risk level hasil koreksi wajib diisi."}],
        ),
        (
            {"aksi": "setujui", "risk_level": "tinggi"},
            [{"field": "risk_level", "pesan": "Risk level hanya diisi untuk aksi koreksi."}],
        ),
        (
            {"aksi": "ajukan_review", "risk_level": "tinggi", "alasan": "Mohon dicek"},
            [{"field": "risk_level", "pesan": "Risk level hanya diisi untuk aksi koreksi."}],
        ),
        (
            {"aksi": "tolak"},
            [{"field": "aksi", "pesan": "Aksi harus salah satu dari: 'setujui', 'koreksi', 'ajukan_review'."}],
        ),
        (
            {"aksi": "koreksi", "risk_level": "merah", "alasan": "Kondisi memburuk"},
            [
                {
                    "field": "risk_level",
                    "pesan": "Risk level harus salah satu dari: 'rendah', 'sedang', 'tinggi', 'kritis'.",
                }
            ],
        ),
        (
            {"aksi": "ajukan_review", "alasan": "Mohon\x00dicek"},
            [{"field": "alasan", "pesan": "Alasan berisi karakter yang tidak diizinkan."}],
        ),
        (
            {"aksi": "ajukan_review", "alasan": "a" * 501},
            [{"field": "alasan", "pesan": "Alasan maksimal 500 karakter."}],
        ),
        ({}, [{"field": "aksi", "pesan": "Aksi wajib diisi."}]),
    ],
)
def test_isian_validasi_tidak_valid(client, dokter, perawat, triase_sedang, sesi_db, isian, errors):
    _, header = perawat if isian.get("aksi") == "ajukan_review" else dokter
    respons = client.post(_url(triase_sedang), json=isian, headers=header)
    assert respons.status_code == 422
    assert respons.get_json()["errors"] == errors
    assert _log(sesi_db, triase_sedang) == []


def test_alasan_review_sudah_cukup_lima_karakter(client, perawat, triase_sedang):
    _, header = perawat
    respons = client.post(_url(triase_sedang), json={"aksi": "ajukan_review", "alasan": "Ragu!"}, headers=header)
    assert respons.status_code == 200


# ---------------------------------------------------------------- satu transaksi


def test_status_tidak_berubah_bila_log_audit_gagal(app, dokter, triase_sedang, sesi_db, monkeypatch):
    def gagal(*_args, **_kwargs):
        raise RuntimeError("log audit gagal ditulis")

    monkeypatch.setattr(AuditLogger, "catat", gagal)
    _, header = dokter
    respons = app.test_client().post(_url(triase_sedang), json={"aksi": "setujui"}, headers=header)

    assert respons.status_code == 500
    sesi_db.refresh(triase_sedang)
    assert triase_sedang.status_validasi == StatusValidasi.MENUNGGU
    assert triase_sedang.divalidasi_oleh is None
