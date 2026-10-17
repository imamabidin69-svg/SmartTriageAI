"""Kelas request yang menyimpan berkas unggahan di memori saja.

Bawaan Werkzeug menulis unggahan di atas 500 KB ke berkas sementara di disk. Foto layar alat tidak
boleh menyentuh disk (Desain 2.4 dan 6.3), jadi semua berkas ditampung di memori lalu dibuang
setelah request selesai. Ukurannya sudah dibatasi MAX_CONTENT_LENGTH.
"""

import io
from typing import IO

from flask import Request


class RequestTanpaBerkasSementara(Request):
    def _get_file_stream(
        self,
        total_content_length: int | None,
        content_type: str | None,
        filename: str | None = None,
        content_length: int | None = None,
    ) -> IO[bytes]:
        del total_content_length, content_type, filename, content_length
        return io.BytesIO()
