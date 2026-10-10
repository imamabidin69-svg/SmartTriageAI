"""Penyedia JSON Flask yang menganggap JSON bersarang terlalu dalam sebagai JSON tidak valid."""

from typing import Any

from flask.json.provider import DefaultJSONProvider


class PenyediaJson(DefaultJSONProvider):
    def loads(self, s: str | bytes, **kwargs: Any) -> Any:
        try:
            return super().loads(s, **kwargs)
        except RecursionError as galat:
            # Tanpa ini, body seperti "[[[[..." menjadi error 500 dan traceback di log untuk setiap request.
            # Sebagai ValueError, request.get_json(silent=True) mengembalikan None dan klien menerima 400.
            raise ValueError("Struktur JSON terlalu dalam.") from galat
