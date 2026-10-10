"""PengukurDurasi (Desain NFR-02): mencatat durasi setiap request sebagai log JSON."""

import logging
import time

from flask import Flask, Response, g, request

logger = logging.getLogger("smarttriage.request")


def pasang_pengukur_durasi(app: Flask) -> None:
    @app.before_request
    def _mulai() -> None:
        g.waktu_mulai = time.perf_counter()

    @app.after_request
    def _catat(respons: Response) -> Response:
        mulai = g.pop("waktu_mulai", None)
        if mulai is not None:
            logger.info(
                "request selesai",
                extra={
                    "metode": request.method,
                    "endpoint": request.endpoint,
                    "path": request.path,
                    "status": respons.status_code,
                    "durasi_ms": round((time.perf_counter() - mulai) * 1000, 1),
                },
            )
        return respons
