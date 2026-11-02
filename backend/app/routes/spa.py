"""SpaRoute: menyajikan hasil build aplikasi web React (admin dan Eir) dari satu origin (Desain baris 101 dan 432).

Berkas di assets/ diberi nama ber-hash oleh Vite, jadi boleh disimpan peramban selamanya. index.html, service
worker, dan manifest selalu dicek ulang supaya versi baru langsung terpakai. Alamat lain yang bukan berkas
dijawab dengan index.html karena rutenya ditangani React Router di peramban.
"""

from pathlib import Path

from flask import Flask, Response, abort, current_app, send_from_directory
from werkzeug.routing import PathConverter

from app.utils.errors import Tipe, respons_problem

CACHE_ASET = "public, max-age=31536000, immutable"
CACHE_HALAMAN = "no-cache"
# Halaman React: semua skrip dan gaya dari origin sendiri (font Inter juga di-hosting sendiri). blob: dipakai
# untuk rekaman suara Eir. Tidak ada skrip inline karena service worker didaftarkan lewat registerSW.js.
CSP_WEB = (
    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: blob:; font-src 'self'; "
    "connect-src 'self'; media-src 'self' blob:; worker-src 'self'; manifest-src 'self'; "
    "base-uri 'self'; form-action 'self'; frame-ancestors 'none'; object-src 'none'"
)


class PathWeb(PathConverter):
    """Seperti <path:...> tetapi tidak pernah cocok dengan /api, supaya alamat API yang tidak ada tetap 404 atau 405
    dalam format Problem Details dan tidak dijawab halaman React."""

    regex = r"(?!api(?:/|$))[^/].*?"


def _folder_web() -> Path:
    return Path(current_app.config["WEB_DIST_PATH"])


def _kirim(folder: Path, nama: str) -> Response:
    respons = send_from_directory(folder, nama, max_age=None)
    respons.headers["Cache-Control"] = CACHE_ASET if nama.startswith("assets/") else CACHE_HALAMAN
    respons.headers["Content-Security-Policy"] = CSP_WEB
    return respons


def sajikan_web(path: str = "") -> Response:
    folder = _folder_web()
    if not (folder / "index.html").is_file():
        return respons_problem(
            404,
            Tipe.TIDAK_DITEMUKAN,
            "Aplikasi web belum dibangun",
            "Jalankan npm run build di folder web, atau buka server Vite saat development.",
        )
    berkas = (folder / path).resolve()
    if path and berkas.is_relative_to(folder.resolve()) and berkas.is_file():
        return _kirim(folder, path)
    if "." in Path(path).name:
        # Berkas statis yang tidak ada (misalnya aset lama setelah rilis baru) tidak boleh dijawab index.html.
        abort(404)
    return _kirim(folder, "index.html")


def daftarkan_web(app: Flask) -> None:
    app.url_map.converters["web"] = PathWeb
    app.add_url_rule("/", "web_indeks", sajikan_web, methods=["GET"])
    app.add_url_rule("/<web:path>", "web", sajikan_web, methods=["GET"])
