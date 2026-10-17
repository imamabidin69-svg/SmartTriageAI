"""Kelola staf oleh admin dan ganti password sendiri (FR-01, Desain 2.1, keputusan K7, K18, D1-D6)."""

import uuid

import pytest
from bantuan import PASSWORD_TES, header_masuk, login_mobile
from sqlalchemy import select

from app.models import LogAudit, Pengguna
from app.models.enums import AksiAudit, Peran
from app.services import staf_service
from app.services.staf_service import HURUF_PASSWORD, PANJANG_PASSWORD_SEMENTARA, buat_password_sementara
from app.utils.errors import Tipe

URL = "/api/v1/admin/staf"
URL_PASSWORD = "/api/v1/auth/password"
STAF_BARU = {"nama": "Ns. Maya Sari", "email": "maya.sari@smarttriage.demo", "peran": "perawat"}


@pytest.fixture
def admin(masuk):
    return masuk(Peran.ADMIN)


def _log(sesi_db, aksi):
    return sesi_db.scalars(select(LogAudit).where(LogAudit.aksi == aksi).order_by(LogAudit.waktu)).all()


def _url(staf) -> str:
    return f"{URL}/{staf.id_pengguna}"


# ---------------------------------------------------------------- password sementara


def test_password_sementara_acak_tanpa_karakter_mirip():
    hasil = {buat_password_sementara() for _ in range(50)}
    assert len(hasil) == 50
    for password in hasil:
        assert len(password) == PANJANG_PASSWORD_SEMENTARA
        assert set(password) <= set(HURUF_PASSWORD)
    assert not set("0Oo1lI") & set(HURUF_PASSWORD)


# ---------------------------------------------------------------- tambah staf


def test_admin_menambah_staf_dengan_password_sementara(client, admin, sesi_db):
    pengguna_admin, header = admin
    respons = client.post(URL, json={**STAF_BARU, "email": " Maya.Sari@SmartTriage.demo "}, headers=header)

    assert respons.status_code == 201
    isi = respons.get_json()
    staf = isi["staf"]
    assert (staf["nama"], staf["email"], staf["peran"], staf["is_active"]) == (
        "Ns. Maya Sari",
        "maya.sari@smarttriage.demo",
        "perawat",
        True,
    )
    assert "password_hash" not in staf
    password = isi["password_sementara"]
    assert len(password) == PANJANG_PASSWORD_SEMENTARA
    # Password sementara benar-benar bisa dipakai login.
    assert login_mobile(client, "maya.sari@smarttriage.demo", password).status_code == 200

    [log] = _log(sesi_db, AksiAudit.TAMBAH_STAF)
    assert log.id_aktor == pengguna_admin.id_pengguna
    assert log.catatan == f"id_pengguna={staf['id_pengguna']}; email=maya.sari@smarttriage.demo; peran=perawat"
    assert password not in log.catatan


def test_password_sementara_tidak_ditulis_ke_log_aplikasi(client, admin, caplog):
    _, header = admin
    password = client.post(URL, json=STAF_BARU, headers=header).get_json()["password_sementara"]
    assert password not in caplog.text


def test_email_yang_sudah_dipakai_dibalas_409(client, admin, sesi_db):
    _, header = admin
    client.post(URL, json=STAF_BARU, headers=header)
    respons = client.post(URL, json={**STAF_BARU, "email": "MAYA.SARI@smarttriage.demo"}, headers=header)
    assert respons.status_code == 409
    assert respons.get_json()["detail"] == "Email ini sudah dipakai akun lain."
    assert len(_log(sesi_db, AksiAudit.TAMBAH_STAF)) == 1


def test_email_bentrok_saat_disimpan_dibalas_409(client, admin, sesi_db, monkeypatch):
    _, header = admin
    client.post(URL, json=STAF_BARU, headers=header)
    # Meniru dua request bersamaan: pemeriksaan awal lolos, tetapi unique constraint menolak.
    monkeypatch.setattr(staf_service.StafService, "_email_belum_dipakai", staticmethod(lambda _email: None))
    respons = client.post(URL, json=STAF_BARU, headers=header)
    assert respons.status_code == 409


@pytest.mark.parametrize(
    ("ubah", "field", "pesan"),
    [
        ({"nama": "  "}, "nama", "Nama wajib diisi."),
        ({"email": "bukan-email"}, "email", "Format email tidak valid."),
        ({"peran": "kepala"}, "peran", "Peran harus salah satu dari: 'perawat', 'dokter', 'admin'."),
        ({"password": "rahasia123"}, "password", "Field password tidak dikenal."),
    ],
)
def test_isian_staf_tidak_valid(client, admin, ubah, field, pesan):
    _, header = admin
    respons = client.post(URL, json={**STAF_BARU, **ubah}, headers=header)
    assert respons.status_code == 422
    assert {"field": field, "pesan": pesan} in respons.get_json()["errors"]


@pytest.mark.parametrize("peran", [Peran.PERAWAT, Peran.DOKTER])
def test_kelola_staf_hanya_untuk_admin(client, masuk, peran, buat_pengguna):
    _, header = masuk(peran)
    lain = buat_pengguna(Peran.PERAWAT)
    assert client.get(URL, headers=header).status_code == 403
    assert client.post(URL, json=STAF_BARU, headers=header).status_code == 403
    assert client.patch(_url(lain), json={"nama": "Baru"}, headers=header).status_code == 403


# ---------------------------------------------------------------- daftar staf


def test_daftar_staf_urut_nama_dan_bisa_difilter(client, admin, buat_pengguna, sesi_db):
    _, header = admin
    for nama, peran, aktif in [
        ("Budi", Peran.DOKTER, True),
        ("Ani", Peran.PERAWAT, False),
        ("Citra", Peran.PERAWAT, True),
    ]:
        pengguna = buat_pengguna(peran, aktif=aktif)
        pengguna.nama = nama
    sesi_db.commit()

    semua = client.get(URL, headers=header).get_json()["items"]
    assert [s["nama"] for s in semua if s["nama"] in {"Ani", "Budi", "Citra"}] == ["Ani", "Budi", "Citra"]
    assert all("password_hash" not in s and "created_at" in s for s in semua)

    perawat = client.get(URL, query_string={"peran": "perawat"}, headers=header).get_json()["items"]
    assert {s["nama"] for s in perawat} == {"Ani", "Citra"}
    aktif = client.get(URL, query_string={"peran": "perawat", "aktif": "true"}, headers=header).get_json()["items"]
    assert [s["nama"] for s in aktif] == ["Citra"]
    nonaktif = client.get(URL, query_string={"aktif": "false"}, headers=header).get_json()["items"]
    assert [s["nama"] for s in nonaktif] == ["Ani"]


# ---------------------------------------------------------------- ubah staf


def test_ubah_data_staf_dicatat_per_field(client, admin, buat_pengguna, sesi_db):
    _, header = admin
    staf = buat_pengguna(Peran.PERAWAT, email="lama@smarttriage.demo")
    isian = {"nama": "Nama  Baru", "email": "baru@smarttriage.demo", "peran": "dokter"}
    respons = client.patch(_url(staf), json=isian, headers=header)

    assert respons.status_code == 200
    isi = respons.get_json()
    assert isi["password_sementara"] is None
    assert (isi["staf"]["nama"], isi["staf"]["email"], isi["staf"]["peran"]) == (
        "Nama Baru",
        "baru@smarttriage.demo",
        "dokter",
    )
    [log] = _log(sesi_db, AksiAudit.UBAH_STAF)
    assert log.catatan == (
        f"id_pengguna={staf.id_pengguna}; email=lama@smarttriage.demo; nama: Pengguna perawat -> Nama Baru; "
        "email: lama@smarttriage.demo -> baru@smarttriage.demo; peran: perawat -> dokter"
    )


def test_patch_tanpa_perubahan_tidak_dicatat(client, admin, buat_pengguna, sesi_db):
    _, header = admin
    staf = buat_pengguna(Peran.PERAWAT)
    respons = client.patch(_url(staf), json={"nama": staf.nama, "is_active": True}, headers=header)
    assert respons.status_code == 200
    assert sesi_db.scalars(select(LogAudit)).all() == []


def test_nonaktifkan_lalu_aktifkan_staf(client, admin, buat_pengguna, sesi_db):
    _, header = admin
    staf = buat_pengguna(Peran.DOKTER)
    header_staf = header_masuk(client, staf.email)

    respons = client.patch(_url(staf), json={"is_active": False}, headers=header)
    assert respons.get_json()["staf"]["is_active"] is False
    # Sesi yang sedang berjalan langsung ditolak (Desain 2.1).
    assert client.get("/api/v1/auth/me", headers=header_staf).status_code == 401
    [log] = _log(sesi_db, AksiAudit.NONAKTIFKAN_STAF)
    assert log.catatan == f"id_pengguna={staf.id_pengguna}; email={staf.email}"

    assert client.patch(_url(staf), json={"is_active": True}, headers=header).get_json()["staf"]["is_active"]
    assert len(_log(sesi_db, AksiAudit.AKTIFKAN_STAF)) == 1


def test_ubah_data_dan_status_dicatat_dua_baris(client, admin, buat_pengguna, sesi_db):
    _, header = admin
    staf = buat_pengguna(Peran.PERAWAT)
    client.patch(_url(staf), json={"nama": "Ganti Nama", "is_active": False}, headers=header)
    aksi = [log.aksi for log in sesi_db.scalars(select(LogAudit))]
    assert sorted(aksi) == sorted([AksiAudit.UBAH_STAF, AksiAudit.NONAKTIFKAN_STAF])


def test_atur_ulang_password(client, admin, buat_pengguna, sesi_db):
    _, header = admin
    staf = buat_pengguna(Peran.PERAWAT)
    respons = client.patch(_url(staf), json={"atur_ulang_password": True}, headers=header)

    password = respons.get_json()["password_sementara"]
    assert len(password) == PANJANG_PASSWORD_SEMENTARA
    assert login_mobile(client, staf.email, PASSWORD_TES).status_code == 401
    assert login_mobile(client, staf.email, password).status_code == 200
    [log] = _log(sesi_db, AksiAudit.ATUR_ULANG_PASSWORD)
    assert log.catatan == f"id_pengguna={staf.id_pengguna}; email={staf.email}"


def test_email_baru_bentrok_saat_disimpan_dibalas_409(client, admin, buat_pengguna, monkeypatch):
    _, header = admin
    staf = buat_pengguna(Peran.PERAWAT)
    lain = buat_pengguna(Peran.DOKTER)
    monkeypatch.setattr(staf_service.StafService, "_email_belum_dipakai", staticmethod(lambda _email: None))
    respons = client.patch(_url(staf), json={"email": lain.email}, headers=header)
    assert respons.status_code == 409
    assert respons.get_json()["detail"] == "Email ini sudah dipakai akun lain."


def test_email_baru_yang_sudah_dipakai_ditolak(client, admin, buat_pengguna):
    _, header = admin
    staf = buat_pengguna(Peran.PERAWAT)
    lain = buat_pengguna(Peran.DOKTER)
    respons = client.patch(_url(staf), json={"email": lain.email}, headers=header)
    assert respons.status_code == 409


@pytest.mark.parametrize(
    ("isi", "pesan"),
    [
        ({}, "Isi minimal satu data staf yang ingin diubah."),
        ({"nama": None}, "Nama harus berupa teks."),
        ({"is_active": None}, "Status aktif harus bernilai true atau false."),
        ({"is_active": "mungkin"}, "Status aktif harus bernilai true atau false."),
    ],
)
def test_patch_staf_tidak_valid(client, admin, buat_pengguna, isi, pesan):
    _, header = admin
    respons = client.patch(_url(buat_pengguna(Peran.PERAWAT)), json=isi, headers=header)
    assert respons.status_code == 422
    assert [e["pesan"] for e in respons.get_json()["errors"]] == [pesan]


def test_staf_tidak_ada(client, admin):
    _, header = admin
    respons = client.patch(f"{URL}/{uuid.uuid4()}", json={"nama": "Siapa"}, headers=header)
    assert respons.status_code == 404
    assert respons.get_json()["detail"] == "Staf tidak ditemukan."


# ---------------------------------------------------------------- menjaga admin (K18)


@pytest.mark.parametrize(
    ("isi", "pesan"),
    [
        ({"is_active": False}, "Anda tidak bisa menonaktifkan akun Anda sendiri."),
        ({"peran": "dokter"}, "Anda tidak bisa mengubah peran akun Anda sendiri."),
    ],
)
def test_admin_tidak_bisa_mengunci_diri_sendiri(client, admin, sesi_db, isi, pesan):
    pengguna, header = admin
    respons = client.patch(_url(pengguna), json=isi, headers=header)
    assert respons.status_code == 409
    assert respons.get_json()["type"] == Tipe.KONFLIK
    assert respons.get_json()["detail"] == pesan
    sesi_db.refresh(pengguna)
    assert (pengguna.is_active, pengguna.peran) == (True, Peran.ADMIN)


def test_admin_boleh_mengubah_nama_sendiri(client, admin):
    pengguna, header = admin
    assert client.patch(_url(pengguna), json={"nama": "Admin IGD"}, headers=header).status_code == 200


def test_admin_nonaktif_boleh_diturunkan(client, admin, buat_pengguna):
    _, header = admin
    # Tidak mengurangi jumlah admin aktif, jadi boleh.
    lain = buat_pengguna(Peran.ADMIN, aktif=False)
    assert client.patch(_url(lain), json={"peran": "dokter"}, headers=header).status_code == 200


def test_admin_lain_boleh_dinonaktifkan_bila_masih_ada_admin_aktif(client, admin, buat_pengguna):
    _, header = admin
    lain = buat_pengguna(Peran.ADMIN)
    assert client.patch(_url(lain), json={"is_active": False}, headers=header).status_code == 200


def test_sistem_tidak_boleh_kehabisan_admin_aktif():
    """Dipanggil langsung karena lewat API admin yang meminta selalu termasuk admin aktif."""
    from app.utils.errors import KonflikError

    staf = Pengguna(id_pengguna=uuid.uuid4(), peran=Peran.ADMIN, is_active=True)
    peminta = Pengguna(id_pengguna=uuid.uuid4(), peran=Peran.ADMIN, is_active=True)
    with pytest.raises(KonflikError, match=r"Harus ada minimal satu admin aktif\."):
        staf_service.StafService._jaga_admin(staf, peminta, None, False, [staf.id_pengguna])
    staf_service.StafService._jaga_admin(staf, peminta, None, False, [staf.id_pengguna, peminta.id_pengguna])


# ---------------------------------------------------------------- ganti password sendiri (D1-D3)


@pytest.mark.parametrize("peran", list(Peran))
def test_semua_peran_bisa_mengganti_password(client, masuk, peran):
    pengguna, header = masuk(peran)
    isian = {"password_lama": PASSWORD_TES, "password_baru": "PasswordBaru456"}
    respons = client.patch(URL_PASSWORD, json=isian, headers=header)

    assert respons.status_code == 204
    assert login_mobile(client, pengguna.email, PASSWORD_TES).status_code == 401
    assert login_mobile(client, pengguna.email, "PasswordBaru456").status_code == 200


def test_ganti_password_tidak_masuk_log_audit(client, masuk, sesi_db):
    _, header = masuk(Peran.PERAWAT)
    client.patch(URL_PASSWORD, json={"password_lama": PASSWORD_TES, "password_baru": "PasswordBaru456"}, headers=header)
    assert sesi_db.scalars(select(LogAudit)).all() == []


@pytest.mark.parametrize(
    ("isian", "field", "pesan"),
    [
        (
            {"password_lama": "Salah123", "password_baru": "PasswordBaru456"},
            "password_lama",
            "Password lama tidak cocok.",
        ),
        (
            {"password_lama": PASSWORD_TES, "password_baru": "pendek"},
            "password_baru",
            "Password baru minimal 8 karakter.",
        ),
        (
            {"password_lama": PASSWORD_TES, "password_baru": "x" * 129},
            "password_baru",
            "Password baru maksimal 128 karakter.",
        ),
        (
            {"password_lama": PASSWORD_TES, "password_baru": PASSWORD_TES},
            "password_baru",
            "Password baru harus berbeda dari password lama.",
        ),
        ({"password_baru": "PasswordBaru456"}, "password_lama", "Password lama wajib diisi."),
    ],
)
def test_ganti_password_tidak_valid(client, masuk, isian, field, pesan):
    pengguna, header = masuk(Peran.DOKTER)
    respons = client.patch(URL_PASSWORD, json=isian, headers=header)
    assert respons.status_code == 422
    assert respons.get_json()["errors"] == [{"field": field, "pesan": pesan}]
    assert login_mobile(client, pengguna.email, PASSWORD_TES).status_code == 200


def test_password_lama_salah_dibatasi(client, masuk):
    _, header = masuk(Peran.PERAWAT)
    salah = {"password_lama": "Salah123", "password_baru": "PasswordBaru456"}
    assert [client.patch(URL_PASSWORD, json=salah, headers=header).status_code for _ in range(5)] == [422] * 5

    benar = {"password_lama": PASSWORD_TES, "password_baru": "PasswordBaru456"}
    respons = client.patch(URL_PASSWORD, json=benar, headers=header)
    assert respons.status_code == 429
    assert respons.get_json()["detail"] == (
        "Terlalu banyak percobaan dengan password lama yang salah. Coba lagi beberapa saat lagi."
    )
    assert int(respons.headers["Retry-After"]) > 0


def test_ganti_password_tanpa_login(client):
    respons = client.patch(URL_PASSWORD, json={"password_lama": "a", "password_baru": "PasswordBaru456"})
    assert respons.status_code == 401
