"""LlmClient untuk Eir: Groq di production, tiruan untuk tes dan development (Desain Gambar 2.23).

LLM hanya dipakai untuk dua tugas, menyusun pertanyaan berikutnya dan merangkum percakapan, keduanya
dengan keluaran JSON Schema. Panggilan dibatasi 10 detik dengan satu kali percobaan ulang (Desain baris 380).
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class LlmTidakTersediaError(RuntimeError):
    """Groq tidak menjawab, waktu habis, atau jawabannya bukan JSON yang diminta."""


class LlmClient(ABC):
    nama: str

    @abstractmethod
    def chat(self, pesan: list[dict[str, str]], skema: dict[str, Any], nama_skema: str) -> dict[str, Any]:
        """Mengirim percakapan dan mengembalikan objek JSON yang sesuai skema."""

    @abstractmethod
    def transkripsi(self, audio: bytes, nama_berkas: str) -> str:
        """Mengubah rekaman suara menjadi teks (mode suara, opsional)."""


class GroqClient(LlmClient):
    nama = "groq"

    def __init__(
        self,
        api_key: str,
        model: str,
        model_suara: str,
        batas_waktu: float,
        klien: Any = None,
    ) -> None:
        if klien is None:
            from groq import Groq

            klien = Groq(api_key=api_key, timeout=batas_waktu, max_retries=1)
        self.klien = klien
        self.model = model
        self.model_suara = model_suara

    def chat(self, pesan: list[dict[str, str]], skema: dict[str, Any], nama_skema: str) -> dict[str, Any]:
        try:
            respons = self.klien.chat.completions.create(
                model=self.model,
                messages=pesan,
                temperature=0.3,
                response_format={
                    "type": "json_schema",
                    "json_schema": {"name": nama_skema, "schema": skema, "strict": True},
                },
            )
            isi = json.loads(respons.choices[0].message.content or "")
        except Exception as galat:
            # Isi pesan tidak ditulis ke log karena berisi keluhan pasien.
            logger.warning("Groq gagal menjawab (%s).", type(galat).__name__)
            raise LlmTidakTersediaError("Groq tidak dapat dihubungi.") from galat
        if not isinstance(isi, dict):
            raise LlmTidakTersediaError("Jawaban Groq bukan objek JSON.")
        return isi

    def transkripsi(self, audio: bytes, nama_berkas: str) -> str:
        try:
            hasil = self.klien.audio.transcriptions.create(
                file=(nama_berkas, audio), model=self.model_suara, language="id", response_format="json"
            )
        except Exception as galat:
            logger.warning("Transkripsi Groq gagal (%s).", type(galat).__name__)
            raise LlmTidakTersediaError("Groq tidak dapat dihubungi.") from galat
        return str(getattr(hasil, "text", "") or "").strip()


class LlmTiruan(LlmClient):
    """Pengganti Groq untuk tes dan development (seperti PembacaLayarTiruan). Tidak pernah dipakai di production.

    Pertanyaan diambil bergiliran dari daftar, sehingga alur halaman Eir bisa dicoba tanpa kunci API.
    """

    nama = "tiruan"
    PERTANYAAN = (
        "Sejak kapan keluhan itu mulai terlihat?",
        "Apakah pasien punya penyakit lama, misalnya darah tinggi, kencing manis, atau sakit jantung?",
        "Obat apa saja yang rutin diminum pasien?",
        "Apakah pasien punya alergi obat atau makanan?",
        "Apakah pasien pernah dioperasi atau dirawat inap sebelumnya?",
        "Sebelum sakit, apakah pasien bisa beraktivitas sendiri?",
        "Apakah ada hal lain yang perlu diketahui tim ICU?",
    )

    def __init__(self) -> None:
        self.panggilan: list[dict[str, Any]] = []

    def chat(self, pesan: list[dict[str, str]], skema: dict[str, Any], nama_skema: str) -> dict[str, Any]:
        self.panggilan.append({"pesan": pesan, "nama_skema": nama_skema})
        jawaban_pasien = [p["content"] for p in pesan if p["role"] == "user"]
        if nama_skema == "ringkasan_keluarga":
            return {
                "kronologi": jawaban_pasien[0][:1000] if jawaban_pasien else "Tidak disebutkan",
                "riwayat_penyakit": jawaban_pasien[1][:1000] if len(jawaban_pasien) > 1 else "Tidak disebutkan",
                "obat_rutin": jawaban_pasien[2][:1000] if len(jawaban_pasien) > 2 else "Tidak disebutkan",
                "alergi": jawaban_pasien[3][:500] if len(jawaban_pasien) > 3 else "Tidak disebutkan",
                "informasi_lain": " ".join(jawaban_pasien[4:])[:1000] or "Tidak disebutkan",
            }
        urutan = (len(jawaban_pasien) - 1) % len(self.PERTANYAAN)
        return {"pertanyaan": self.PERTANYAAN[urutan], "cukup": len(jawaban_pasien) >= len(self.PERTANYAAN)}

    def transkripsi(self, audio: bytes, nama_berkas: str) -> str:
        del nama_berkas
        return "Bapak sesak sejak semalam lalu tidak bisa dibangunkan" if audio else ""
