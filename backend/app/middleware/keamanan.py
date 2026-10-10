"""Header keamanan untuk setiap respons (Tech Stack v2.0 Tabel 4)."""

from flask import Flask, Response, request

CSP_API = "default-src 'none'; frame-ancestors 'none'"


def pasang_header_keamanan(app: Flask) -> None:
    prefiks_dokumentasi = app.config["PREFIKS_DOKUMENTASI"]

    @app.after_request
    def _tambah_header(respons: Response) -> Response:
        header = respons.headers
        header.setdefault("X-Content-Type-Options", "nosniff")
        header.setdefault("X-Frame-Options", "DENY")
        header.setdefault("Referrer-Policy", "no-referrer")
        # Respons API berisi data pasien dan token: jangan disimpan cache peramban atau service worker.
        # CSP untuk halaman React diatur terpisah saat SpaRoute dibuat (Tahap 5).
        if request.path.startswith("/api/") and not request.path.startswith(prefiks_dokumentasi):
            header.setdefault("Content-Security-Policy", CSP_API)
            header.setdefault("Cache-Control", "no-store")
        if app.config["HSTS_AKTIF"]:
            header.setdefault("Strict-Transport-Security", "max-age=31536000")
        return respons
