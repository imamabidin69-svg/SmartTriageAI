"""Kunci baris SELECT ... FOR UPDATE diuji dengan dua request yang benar-benar berjalan bersamaan.

Setiap request memakai koneksinya sendiri dan data di-commit sungguhan, karena kunci baris hanya
berpengaruh antar-transaksi. Jeda kecil disisipkan di dalam transaksi supaya kedua request pasti tumpang
tindih; tanpa kunci, keduanya akan membaca keadaan yang sama.
"""

import threading
import time

import pytest
from bantuan import PASSWORD_TES, header_masuk

from app.extensions import db
from app.models import Kunjungan, LogAudit, Pasien, Pengguna, Triase
from app.models.enums import JenisKelamin, Peran, StatusKunjungan
from app.services import triase_service, validasi_service
from app.services.audit_logger import AuditLogger

pytestmark = [pytest.mark.tanpa_rollback, pytest.mark.usefixtures("data_nyata")]

JEDA = 0.4
ISIAN_TRIASE = {
    "keluhan_utama": "Pusing",
    "gejala": "Pusing berputar sejak pagi tanpa muntah",
    "kategori_keluhan": "Pusing",
    "skala_nyeri": 2,
    "tingkat_kesadaran": "A",
    "tanda_vital": {"td_sistolik": 120, "td_diastolik": 80, "nadi": 80, "laju_napas": 18, "suhu": 36.8, "saturasi": 98},
}


def _siapkan(app):
    with app.app_context():
        perawat = Pengguna(nama="Perawat Uji", email="perawat.konkuren@smarttriage.demo", peran=Peran.PERAWAT)
        perawat.atur_password(PASSWORD_TES)
        db.session.add(perawat)
        db.session.flush()
        pasien = Pasien(
            didaftarkan_oleh=perawat.id_pengguna,
            nama="Pasien Uji",
            perkiraan_usia=40,
            jenis_kelamin=JenisKelamin.PEREMPUAN,
        )
        db.session.add(pasien)
        db.session.commit()
        return perawat.email, pasien.id_pasien


def _bersamaan(app, kirim) -> list:
    """Menjalankan dua request sekaligus dan mengembalikan respons keduanya."""
    mulai = threading.Barrier(2)
    hasil: list = []

    def pekerja():
        klien = app.test_client()
        mulai.wait()
        hasil.append(kirim(klien))

    utas = [threading.Thread(target=pekerja) for _ in range(2)]
    for u in utas:
        u.start()
    for u in utas:
        u.join(timeout=30)
    assert len(hasil) == 2
    return hasil


def _dengan_jeda(fungsi):
    def lambat(*args, **kwargs):
        time.sleep(JEDA)
        return fungsi(*args, **kwargs)

    return lambat


def test_dua_triase_bersamaan_tercatat_awal_dan_ulang(app, monkeypatch):
    email, id_pasien = _siapkan(app)
    with app.app_context():
        kunjungan = Kunjungan(id_pasien=id_pasien)
        db.session.add(kunjungan)
        db.session.commit()
        id_kunjungan = kunjungan.id_kunjungan
    header = header_masuk(app.test_client(), email)
    # Jeda setelah jenis triase ditentukan, sebelum transaksi selesai.
    asli = triase_service.TriaseService._ambil_pemindaian
    monkeypatch.setattr(triase_service.TriaseService, "_ambil_pemindaian", staticmethod(_dengan_jeda(asli)))

    respons = _bersamaan(
        app, lambda klien: klien.post(f"/api/v1/kunjungan/{id_kunjungan}/triase", json=ISIAN_TRIASE, headers=header)
    )
    assert [r.status_code for r in respons] == [201, 201]
    assert sorted(r.get_json()["jenis"] for r in respons) == ["awal", "ulang"]
    with app.app_context():
        assert db.session.query(Triase).filter_by(id_kunjungan=id_kunjungan).count() == 2


def test_dua_registrasi_pasien_yang_sama_hanya_satu_kunjungan_aktif(app, monkeypatch):
    email, id_pasien = _siapkan(app)
    header = header_masuk(app.test_client(), email)
    monkeypatch.setattr(AuditLogger, "catat", _dengan_jeda(AuditLogger.catat))

    respons = _bersamaan(
        app, lambda klien: klien.post("/api/v1/kunjungan", json={"id_pasien": str(id_pasien)}, headers=header)
    )
    assert sorted(r.status_code for r in respons) == [201, 409]
    with app.app_context():
        aktif = db.session.query(Kunjungan).filter_by(id_pasien=id_pasien, status=StatusKunjungan.MENUNGGU).count()
        assert aktif == 1


def test_dua_registrasi_nik_baru_yang_sama_hanya_satu_berhasil(app, monkeypatch):
    email, _ = _siapkan(app)
    header = header_masuk(app.test_client(), email)
    monkeypatch.setattr(AuditLogger, "catat", _dengan_jeda(AuditLogger.catat))
    isi = {"nama": "Pasien Baru", "perkiraan_usia": 30, "jenis_kelamin": "laki_laki", "nik": "3577010101990001"}

    respons = _bersamaan(app, lambda klien: klien.post("/api/v1/kunjungan", json=isi, headers=header))
    assert sorted(r.status_code for r in respons) == [201, 409]
    with app.app_context():
        assert db.session.query(Pasien).filter_by(nik="3577010101990001").count() == 1


def _dokter(app):
    with app.app_context():
        dokter = Pengguna(nama="Dokter Uji", email="dokter.konkuren@smarttriage.demo", peran=Peran.DOKTER)
        dokter.atur_password(PASSWORD_TES)
        db.session.add(dokter)
        db.session.commit()
        return dokter.email


def _triase_tersimpan(app, email_perawat, id_pasien):
    with app.app_context():
        kunjungan = Kunjungan(id_pasien=id_pasien)
        db.session.add(kunjungan)
        db.session.commit()
        id_kunjungan = kunjungan.id_kunjungan
    header = header_masuk(app.test_client(), email_perawat)
    respons = app.test_client().post(f"/api/v1/kunjungan/{id_kunjungan}/triase", json=ISIAN_TRIASE, headers=header)
    return respons.get_json()["id_triase"]


def test_dua_validasi_bersamaan_hanya_satu_berhasil(app, monkeypatch):
    email, id_pasien = _siapkan(app)
    id_triase = _triase_tersimpan(app, email, id_pasien)
    header = header_masuk(app.test_client(), _dokter(app))
    # Jeda setelah baris dikunci dan sebelum status diubah; tanpa kunci keduanya membaca status menunggu.
    asli = validasi_service.ValidasiService._periksa_status
    monkeypatch.setattr(validasi_service.ValidasiService, "_periksa_status", staticmethod(_dengan_jeda(asli)))
    isian = [{"aksi": "setujui"}, {"aksi": "koreksi", "risk_level": "kritis", "alasan": "Kondisi memburuk"}]

    respons = _bersamaan(
        app,
        lambda klien: klien.post(f"/api/v1/triase/{id_triase}/validasi", json=isian.pop(), headers=header),
    )
    assert sorted(r.status_code for r in respons) == [200, 409]
    with app.app_context():
        assert db.session.query(LogAudit).filter_by(id_triase=id_triase).count() == 1
