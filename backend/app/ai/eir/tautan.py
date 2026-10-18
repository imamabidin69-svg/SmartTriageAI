"""TautanEir: token bertanda tangan untuk membuka Eir tanpa akun (Desain 2.8 dan 7.1).

Ada dua jenis token dengan salt berbeda, sehingga satu tidak bisa dipakai sebagai yang lain:
token tautan (isi kode QR, menunjuk kunjungan) dan token sesi (menunjuk satu sesi Eir).
Keduanya berlaku dua jam.
"""

import uuid

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.utils.errors import AplikasiError, Tipe

SALT_TAUTAN = "smarttriage-tautan-eir"
SALT_SESI = "smarttriage-sesi-eir"


class TokenEirTidakValidError(AplikasiError):
    status = 401
    tipe = Tipe.TOKEN_TIDAK_VALID
    judul = "Tautan Eir tidak valid"


class TokenEirKedaluwarsaError(AplikasiError):
    status = 401
    tipe = Tipe.TOKEN_KEDALUWARSA
    judul = "Tautan Eir kedaluwarsa"


class _TokenBertanda:
    def __init__(self, secret_key: str, salt: str, umur_detik: int) -> None:
        self.serializer = URLSafeTimedSerializer(secret_key, salt=salt)
        self.umur_detik = umur_detik

    def _buat(self, id_objek: uuid.UUID) -> str:
        return self.serializer.dumps(str(id_objek))

    def _baca(self, token: str, pesan_kedaluwarsa: str) -> uuid.UUID:
        try:
            isi = self.serializer.loads(token, max_age=self.umur_detik)
            return uuid.UUID(str(isi))
        except SignatureExpired as galat:
            raise TokenEirKedaluwarsaError(pesan_kedaluwarsa) from galat
        except (BadSignature, ValueError) as galat:
            raise TokenEirTidakValidError("Tautan tidak dikenali. Minta kode QR baru ke perawat.") from galat


class TautanEir(_TokenBertanda):
    def __init__(self, secret_key: str, umur_detik: int) -> None:
        super().__init__(secret_key, SALT_TAUTAN, umur_detik)

    def buat(self, id_kunjungan: uuid.UUID) -> str:
        return self._buat(id_kunjungan)

    def baca(self, token: str) -> uuid.UUID:
        return self._baca(token, "Kode QR sudah lebih dari dua jam. Minta kode QR baru ke perawat.")


class TokenSesiEir(_TokenBertanda):
    def __init__(self, secret_key: str, umur_detik: int) -> None:
        super().__init__(secret_key, SALT_SESI, umur_detik)

    def buat(self, id_sesi: uuid.UUID) -> str:
        return self._buat(id_sesi)

    def baca(self, token: str, id_sesi: uuid.UUID) -> None:
        """Token sesi hanya berlaku untuk sesi yang namanya ada di alamat."""
        if self._baca(token, "Sesi Eir sudah berakhir. Silakan sampaikan keluhan langsung ke perawat.") != id_sesi:
            raise TokenEirTidakValidError("Token tidak berlaku untuk sesi ini.")
