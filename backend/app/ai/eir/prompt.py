"""PembersihIdentitas, PenyusunPrompt, dan PemeriksaKeluaran untuk Eir (Desain 2.8, 7.2, dan 7.4).

Nama dan NIK pasien tidak pernah dikirim ke Groq. Jawaban LLM diperiksa sebelum ditampilkan supaya Eir tidak
memberi diagnosis, memperkirakan kondisi pasien, menyarankan obat, atau menyebut level prioritas.
"""

import re
from typing import Any

from app.ai.eir.panduan import Panduan

PANJANG_MAKS_PERTANYAAN = 300

ATURAN_EIR = """Kamu adalah Eir, asisten yang membantu tim ICU mengenal riwayat kesehatan pasien. Pasien sedang
dirawat di ICU dan belum bisa ditanya langsung, jadi kamu mengobrol dengan {pengisi}. Tugasmu hanya mengumpulkan
keterangan untuk perawat ICU.

Topik yang perlu digali: kronologi sebelum masuk ICU, riwayat penyakit, obat rutin, alergi, riwayat operasi
atau rawat inap, serta kebiasaan dan kondisi sehari-hari pasien.

Aturan:
- Ajukan tepat satu pertanyaan pendek setiap giliran, dengan bahasa Indonesia sehari-hari yang sopan dan empatik.
- Jangan memberi diagnosis atau dugaan penyakit.
- Jangan memperkirakan kondisi pasien, peluang sembuh, atau lama perawatan.
- Jangan menyarankan obat, dosis, atau tindakan pengobatan.
- Jangan menyebut level prioritas, skor, atau tingkat kegawatan pasien.
- Jangan menanyakan nama, NIK, alamat, atau nomor telepon.
- Jangan mengulang pertanyaan yang sudah dijawab. Bila keluarga tidak tahu, lanjut ke topik lain.
- Isi "cukup" dengan true hanya bila kronologi, riwayat penyakit, obat rutin, dan alergi sudah tergali.

Panduan pertanyaan yang relevan:

{panduan}"""

ATURAN_RINGKASAN = """Rangkum percakapan berikut untuk perawat ICU. Tulis hanya yang disampaikan {pengisi},
tanpa menambah dugaan penyakit, obat, atau perkiraan kondisi. Tulis "Tidak disebutkan" untuk topik yang tidak
dibahas, dan "Tidak tahu" bila keluarga menyatakan tidak tahu.

- kronologi: urutan kejadian sebelum pasien masuk ICU.
- riwayat_penyakit: penyakit lama atau yang sedang dikontrol.
- obat_rutin: nama obat yang rutin dipakai dan kapan terakhir dipakai, sesuai kata keluarga.
- alergi: alergi obat, makanan, atau bahan lain beserta reaksinya.
- informasi_lain: riwayat operasi, rawat inap, alat di tubuh, kehamilan, kebiasaan, dan keinginan pasien."""

SKEMA_PERTANYAAN: dict[str, Any] = {
    "type": "object",
    "properties": {
        "pertanyaan": {"type": "string", "description": "Satu pertanyaan berikutnya untuk pengisi."},
        "cukup": {"type": "boolean", "description": "true bila keterangan sudah cukup untuk perawat."},
    },
    "required": ["pertanyaan", "cukup"],
    "additionalProperties": False,
}

KOLOM_RINGKASAN = ("kronologi", "riwayat_penyakit", "obat_rutin", "alergi", "informasi_lain")
SKEMA_RINGKASAN: dict[str, Any] = {
    "type": "object",
    "properties": {kolom: {"type": "string"} for kolom in KOLOM_RINGKASAN},
    "required": list(KOLOM_RINGKASAN),
    "additionalProperties": False,
}

NAMA_PENGISI = {"pasien": "pasien", "keluarga": "keluarga pasien"}


class PembersihIdentitas:
    """Mengganti nama pasien, NIK, dan nomor telepon di teks sebelum dikirim ke Groq (Desain Tabel 7.2)."""

    POLA_NIK = re.compile(r"\b\d{16}\b")
    POLA_TELEPON = re.compile(r"(\+62|\b62|\b0)[\s-]?8[\d\s-]{7,13}\d\b")

    def __init__(self, nama: str | None, nik: str | None = None, no_telepon: str | None = None) -> None:
        # Bagian nama yang terlalu pendek ("A", "Al") tidak dicari supaya kata biasa tidak ikut terhapus.
        bagian = sorted({b for b in (nama or "").split() if len(b) >= 3}, key=len, reverse=True)
        self.pola_nama = (
            re.compile(r"\b(" + "|".join(re.escape(b) for b in bagian) + r")\b", re.IGNORECASE) if bagian else None
        )
        self.nilai_pasti = [v for v in (nik, no_telepon) if v]

    def bersihkan(self, teks: str) -> str:
        for nilai in self.nilai_pasti:
            teks = teks.replace(nilai, "[disamarkan]")
        teks = self.POLA_NIK.sub("[nik]", teks)
        teks = self.POLA_TELEPON.sub("[telepon]", teks)
        if self.pola_nama is not None:
            teks = self.pola_nama.sub("[nama]", teks)
        return teks


def _riwayat_pesan(transkrip: list[dict[str, Any]], pembersih: PembersihIdentitas) -> list[dict[str, str]]:
    return [
        {
            "role": "assistant" if item["peran"] == "eir" else "user",
            "content": item["teks"] if item["peran"] == "eir" else pembersih.bersihkan(item["teks"]),
        }
        for item in transkrip
    ]


class PenyusunPrompt:
    def __init__(self, pembersih: PembersihIdentitas, pengisi: str) -> None:
        self.pembersih = pembersih
        self.pengisi = NAMA_PENGISI.get(pengisi, pengisi)

    def susun(self, panduan: list[Panduan], riwayat: list[dict[str, Any]]) -> list[dict[str, str]]:
        teks_panduan = "\n\n---\n\n".join(p.isi for p in panduan)
        sistem = ATURAN_EIR.format(pengisi=self.pengisi, panduan=teks_panduan)
        return [{"role": "system", "content": sistem}, *_riwayat_pesan(riwayat, self.pembersih)]

    def susun_ringkasan(self, riwayat: list[dict[str, Any]]) -> list[dict[str, str]]:
        sistem = ATURAN_RINGKASAN.format(pengisi=self.pengisi)
        return [{"role": "system", "content": sistem}, *_riwayat_pesan(riwayat, self.pembersih)]


class PemeriksaKeluaran:
    """Menolak pertanyaan LLM yang berisi diagnosis, perkiraan kondisi, saran obat, atau level (Desain 2.8)."""

    POLA_TERLARANG = re.compile(
        r"diagnosis|didiagnosis|diagnosa"
        r"|(anda|kamu|bapak|ibu|pasien)\s+(mungkin|kemungkinan|sepertinya|tampaknya)?\s*"
        r"(terkena|menderita|mengidap|terserang|mengalami penyakit)"
        r"|kemungkinan besar (ini|anda|karena)|gejala (khas|dari) penyakit"
        r"|(sebaiknya|disarankan|saran saya|silakan|cobalah|coba)\s+"
        r"(minum|mengonsumsi|konsumsi|memakai|pakai|menggunakan|gunakan|meminum)\b"
        r"|\bdosis\b|\d+\s?(mg|ml|tablet|kapsul)\b"
        r"|risk level|level (risiko|triase|kegawatan|prioritas)|tingkat kegawatan|zona (merah|kuning|hijau)"
        r"|skor news|peluang (sembuh|hidup|meninggal|memburuk)|harapan hidup|prognosis"
        r"|(pasti|akan|bisa) (sembuh|membaik|meninggal|pulih)\b"
        r"|(termasuk|kategori) (gawat|darurat|kritis|ringan)",
        re.IGNORECASE,
    )

    def aman(self, teks: str) -> bool:
        teks = teks.strip()
        return 0 < len(teks) <= PANJANG_MAKS_PERTANYAAN and not self.POLA_TERLARANG.search(teks)
