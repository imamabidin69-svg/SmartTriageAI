"""Kursor paginasi berbasis (waktu, id) untuk riwayat dan log audit (Desain 2.9).

Kursor dikirim ke klien sebagai string base64 yang tidak perlu diurai. Isinya waktu dan id baris
terakhir di halaman sebelumnya, sehingga halaman berikutnya tetap konsisten walau ada baris baru.
"""

import base64
import binascii
import json
import uuid
from dataclasses import dataclass
from datetime import datetime

from app.utils.errors import ValidasiGagalError

UKURAN_BAWAAN = 20
UKURAN_MAKSIMUM = 50


@dataclass(frozen=True)
class Kursor:
    waktu: datetime
    id: uuid.UUID

    def enkode(self) -> str:
        isi = json.dumps({"w": self.waktu.isoformat(), "i": str(self.id)}, separators=(",", ":"))
        return base64.urlsafe_b64encode(isi.encode()).decode().rstrip("=")

    @classmethod
    def dekode(cls, teks: str) -> "Kursor":
        try:
            isi = base64.urlsafe_b64decode(teks + "=" * (-len(teks) % 4))
            data = json.loads(isi)
            waktu = datetime.fromisoformat(data["w"])
            if waktu.tzinfo is None:
                raise ValueError("waktu tanpa zona")
            return cls(waktu=waktu, id=uuid.UUID(data["i"]))
        except (binascii.Error, UnicodeDecodeError, ValueError, KeyError, TypeError) as galat:
            raise ValidasiGagalError(
                [{"field": "kursor", "pesan": "Kursor tidak valid. Muat ulang dari halaman pertama."}]
            ) from galat
