"""Log terstruktur dalam format JSON, satu baris per kejadian."""

import json
import logging
import sys
from datetime import UTC, datetime

FIELD_TAMBAHAN = ("metode", "endpoint", "path", "status", "durasi_ms")


class PemformatJson(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data = {
            "waktu": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "pesan": record.getMessage(),
        }
        for field in FIELD_TAMBAHAN:
            if hasattr(record, field):
                data[field] = getattr(record, field)
        if record.exc_info:
            data["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(data, ensure_ascii=False)


class _HandlerSmartTriage(logging.StreamHandler):
    """Penanda supaya handler tidak terpasang dua kali bila create_app dipanggil berulang."""


def atur_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger()
    if any(isinstance(handler, _HandlerSmartTriage) for handler in root.handlers):
        return
    handler = _HandlerSmartTriage(sys.stdout)
    handler.setFormatter(PemformatJson())
    root.addHandler(handler)
    root.setLevel(level)
