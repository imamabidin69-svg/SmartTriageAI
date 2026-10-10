"""Batas 5 kali gagal per 15 menit, dihitung terpisah per email dan per alamat IP (Desain 2.1)."""

import json
import time
from types import SimpleNamespace

import limits.storage.memory
from bantuan import PASSWORD_TES, login_web

from app import create_app
from app.models.enums import Peran
from app.utils.errors import Tipe

BATAS = 5


def _login(client, email, password, ip="10.0.0.1", **headers):
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
        environ_base={"REMOTE_ADDR": ip},
        headers=headers,
    )


def test_percobaan_keenam_ditolak_walau_password_benar(client, buat_pengguna):
    perawat = buat_pengguna(Peran.PERAWAT)
    status = [_login(client, perawat.email, "Salah").status_code for _ in range(BATAS)]
    assert status == [401] * BATAS

    respons = _login(client, perawat.email, PASSWORD_TES)
    assert respons.status_code == 429
    assert respons.content_type == "application/problem+json"
    assert respons.get_json()["type"] == Tipe.TERLALU_BANYAK_PERCOBAAN
    # Dikunci sekitar 15 menit (NFR-01), bukan hanya beberapa detik.
    assert 840 <= int(respons.headers["Retry-After"]) <= 900
    assert respons.headers["X-RateLimit-Limit"] == "5"
    assert respons.headers["X-RateLimit-Remaining"] == "0"
    assert respons.headers.getlist("Set-Cookie") == []


def test_variasi_spasi_dan_huruf_besar_dihitung_email_yang_sama(client, buat_pengguna):
    perawat = buat_pengguna(Peran.PERAWAT, email="perawat.jaga@smarttriage.demo")
    variasi = [
        "perawat.jaga@smarttriage.demo",
        " perawat.jaga@smarttriage.demo",
        "Perawat.Jaga@smarttriage.demo",
        "PERAWAT.JAGA@SMARTTRIAGE.DEMO ",
        "\tperawat.jaga@SmartTriage.demo",
    ]
    # Tiap percobaan memakai IP berbeda supaya yang teruji hanya batas per email.
    for i, email in enumerate(variasi):
        assert _login(client, email, "Salah", ip=f"10.1.0.{i}").status_code == 401
    assert _login(client, perawat.email, PASSWORD_TES, ip="10.1.0.99").status_code == 429


def test_batas_per_ip_berlaku_lintas_email(client):
    # Opsi (b): satu IP yang gagal lima kali pada email berbeda juga dikunci.
    for i in range(BATAS):
        assert _login(client, f"tebakan{i}@smarttriage.demo", "Salah", ip="10.2.0.1").status_code == 401
    assert _login(client, "lain@smarttriage.demo", "Salah", ip="10.2.0.1").status_code == 429
    # IP lain dengan email lain tidak terpengaruh.
    assert _login(client, "lain@smarttriage.demo", "Salah", ip="10.2.0.2").status_code == 401


def test_login_berhasil_tidak_dihitung(client, buat_pengguna):
    dokter = buat_pengguna(Peran.DOKTER)
    status = [login_web(client, dokter.email).status_code for _ in range(BATAS + 2)]
    assert status == [200] * (BATAS + 2)


def test_akun_nonaktif_dihitung_sebagai_percobaan_gagal(client, buat_pengguna):
    perawat = buat_pengguna(Peran.PERAWAT, aktif=False)
    status = [_login(client, perawat.email, PASSWORD_TES).status_code for _ in range(BATAS + 1)]
    assert status == [403] * BATAS + [429]


def test_isian_tidak_valid_tidak_dihitung(client, buat_pengguna):
    perawat = buat_pengguna(Peran.PERAWAT)
    for _ in range(BATAS + 1):
        assert client.post("/api/v1/auth/login", json={"email": perawat.email}).status_code == 422
    assert login_web(client, perawat.email).status_code == 200


def test_x_forwarded_for_palsu_diabaikan_tanpa_proxy_tepercaya(client):
    for i in range(BATAS):
        respons = _login(
            client, f"palsu{i}@smarttriage.demo", "Salah", ip="10.3.0.1", **{"X-Forwarded-For": f"1.2.3.{i}"}
        )
        assert respons.status_code == 401
    respons = _login(client, "palsu9@smarttriage.demo", "Salah", ip="10.3.0.1", **{"X-Forwarded-For": "9.9.9.9"})
    assert respons.status_code == 429


def test_jendela_bergeser_menghitung_kegagalan_15_menit_terakhir(client, buat_pengguna, monkeypatch):
    """SKPL Gambar 4.2: "gagal 5 kali dalam 15 menit terakhir", bukan jendela tetap yang direset serentak."""
    jam = [time.time()]
    monkeypatch.setattr(limits.storage.memory, "time", SimpleNamespace(time=lambda: jam[0]))
    perawat = buat_pengguna(Peran.PERAWAT)

    assert _login(client, perawat.email, "Salah").status_code == 401  # menit ke-0
    jam[0] += 14 * 60 + 50
    for _ in range(BATAS - 1):  # menit ke-14:50
        assert _login(client, perawat.email, "Salah").status_code == 401
    jam[0] += 11  # menit ke-15:01, kegagalan pertama sudah lewat 15 menit
    assert _login(client, perawat.email, "Salah").status_code == 401
    # Empat kegagalan pada 14:50 ditambah satu pada 15:01 sudah lima dalam 15 menit terakhir.
    assert _login(client, perawat.email, PASSWORD_TES).status_code == 429
    jam[0] += 15 * 60
    assert _login(client, perawat.email, PASSWORD_TES).status_code == 200


def test_email_sangat_panjang_ditolak_cepat(client):
    # Validasi email berbiaya kuadratik; kunci pembatas tidak boleh memproses input sepanjang ini.
    mulai = time.perf_counter()
    respons = client.post("/api/v1/auth/login", json={"email": "a" * 1_000_000 + "@smarttriage.demo", "password": "x"})
    assert respons.status_code == 422
    assert time.perf_counter() - mulai < 2


def test_body_json_berupa_string_tetap_memakai_kunci_email(client, buat_pengguna):
    perawat = buat_pengguna(Peran.PERAWAT)
    for i in range(BATAS):
        assert _login(client, perawat.email, "Salah", ip=f"10.4.0.{i}").status_code == 401
    isi = json.dumps(json.dumps({"email": f" {perawat.email.upper()}", "password": PASSWORD_TES}))
    respons = client.post(
        "/api/v1/auth/login", data=isi, content_type="application/json", environ_base={"REMOTE_ADDR": "10.4.0.99"}
    )
    assert respons.status_code == 429


def test_batas_per_ip_memakai_ip_klien_di_belakang_proxy_tepercaya(konfigurasi_app):
    klien = create_app({**konfigurasi_app, "JUMLAH_PROXY": 1}).test_client()

    def login(email, ip_klien):
        return klien.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "Salah"},
            environ_base={"REMOTE_ADDR": "10.9.9.9"},
            headers={"X-Forwarded-For": ip_klien},
        )

    for i in range(BATAS):
        assert login(f"penyerang{i}@smarttriage.demo", "203.0.113.7").status_code == 401
    assert login("penyerang9@smarttriage.demo", "203.0.113.7").status_code == 429
    # Klien lain di belakang proxy yang sama tidak ikut terkunci.
    assert login("perawat.lain@smarttriage.demo", "198.51.100.20").status_code == 401
