"""EirAgent: agen berbasis alur untuk anamnesis (Desain 7.2, Gambar 2.22 dan 2.24).

Urutan langkah dipegang kode, bukan LLM: setiap pesan diperiksa tanda bahayanya lebih dulu, lalu panduan
diambil dengan TF-IDF, prompt disusun tanpa identitas, dan Groq menyusun pertanyaan berikutnya. LLM tidak
punya akses tulis ke tabel triase; ringkasannya hanya disimpan di sesi sebagai draf.
"""

import logging
from dataclasses import dataclass
from datetime import datetime

from pydantic import ValidationError

from app.ai.eir.llm import LlmClient, LlmTidakTersediaError
from app.ai.eir.panduan import GuidelineRetriever, Panduan
from app.ai.eir.prompt import (
    SKEMA_PERTANYAAN,
    SKEMA_RINGKASAN,
    PembersihIdentitas,
    PemeriksaKeluaran,
    PenyusunPrompt,
)
from app.ai.eir.tanda_bahaya import ARAHAN_TANDA_BAHAYA, RedFlagDetector, TandaBahaya
from app.models.enums import StatusSesiEir
from app.models.sesi_eir import PERAN_EIR, PERAN_PENGISI, SesiEir
from app.utils.schemas import RingkasanTriase

logger = logging.getLogger(__name__)

PERTANYAAN_PEMBUKA = (
    "Halo, saya Eir. Saya akan menanyakan beberapa hal tentang keluhan supaya perawat bisa lebih cepat "
    "memahaminya. Keluhan apa yang paling mengganggu saat ini?"
)
PERTANYAAN_UMUM = "Apakah ada hal lain tentang keluhan ini yang ingin disampaikan?"
PENUTUP = (
    "Terima kasih, jawaban sudah kami teruskan ke perawat. Silakan tetap menunggu di ruang tunggu sampai "
    "dipanggil. Bila keluhan bertambah berat, segera beri tahu perawat."
)


@dataclass(frozen=True)
class Balasan:
    pesan: str
    status: StatusSesiEir
    jumlah_jawaban: int
    boleh_selesai: bool
    tanda_bahaya: TandaBahaya | None = None


class EirAgent:
    def __init__(
        self,
        detektor: RedFlagDetector,
        retriever: GuidelineRetriever | None,
        llm: LlmClient | None,
        min_jawaban: int,
        maks_jawaban: int,
        pemeriksa: PemeriksaKeluaran | None = None,
    ) -> None:
        self.detektor = detektor
        self.retriever = retriever
        self.llm = llm
        self.min_jawaban = min_jawaban
        self.maks_jawaban = maks_jawaban
        self.pemeriksa = pemeriksa or PemeriksaKeluaran()

    @property
    def tersedia(self) -> bool:
        return self.retriever is not None and self.llm is not None

    def mulai(self, sesi: SesiEir, waktu: datetime) -> str:
        """Pertanyaan pertama selalu sama dan tidak memanggil LLM."""
        sesi.tambah_pesan(PERAN_EIR, PERTANYAAN_PEMBUKA, waktu)
        return PERTANYAAN_PEMBUKA

    def _balasan(self, sesi: SesiEir, pesan: str, tanda: TandaBahaya | None = None) -> Balasan:
        jumlah = sesi.jumlah_jawaban
        return Balasan(pesan, sesi.status, jumlah, sesi.berjalan and jumlah >= self.min_jawaban, tanda)

    def proses(self, sesi: SesiEir, teks: str, pembersih: PembersihIdentitas, waktu: datetime) -> Balasan:
        """Memproses satu jawaban. Melempar LlmTidakTersediaError setelah jawaban dicatat di sesi."""
        sesi.tambah_pesan(PERAN_PENGISI, teks, waktu)

        tanda = self.detektor.periksa(teks)
        if tanda is not None:
            sesi.hentikan(tanda.label, waktu)
            sesi.tambah_pesan(PERAN_EIR, ARAHAN_TANDA_BAHAYA, waktu)
            return self._balasan(sesi, ARAHAN_TANDA_BAHAYA, tanda)

        if not self.tersedia:
            raise LlmTidakTersediaError("Eir belum dikonfigurasi.")
        if sesi.jumlah_jawaban >= self.maks_jawaban:
            # Batas giliran tercapai: ringkasan dibuat otomatis (keputusan E6).
            return self.ringkas(sesi, pembersih, waktu)

        penyusun = PenyusunPrompt(pembersih, sesi.pengisi.value)
        panduan = self.retriever.cari(self._kueri(sesi))
        hasil = self.llm.chat(penyusun.susun(panduan, sesi.transkrip), SKEMA_PERTANYAAN, "pertanyaan_berikutnya")
        if bool(hasil.get("cukup")) and sesi.jumlah_jawaban >= self.min_jawaban:
            return self.ringkas(sesi, pembersih, waktu)

        pertanyaan = str(hasil.get("pertanyaan", "")).strip()
        if not self.pemeriksa.aman(pertanyaan):
            # Keputusan E3: jawaban yang melanggar larangan diganti pertanyaan inti dari panduan.
            logger.warning("Pertanyaan dari LLM ditolak PemeriksaKeluaran; memakai pertanyaan panduan.")
            pertanyaan = self._pertanyaan_cadangan(sesi, panduan)
        sesi.tambah_pesan(PERAN_EIR, pertanyaan, waktu)
        return self._balasan(sesi, pertanyaan)

    def ringkas(self, sesi: SesiEir, pembersih: PembersihIdentitas, waktu: datetime) -> Balasan:
        if self.llm is None:
            raise LlmTidakTersediaError("Eir belum dikonfigurasi.")
        penyusun = PenyusunPrompt(pembersih, sesi.pengisi.value)
        isi = self.llm.chat(penyusun.susun_ringkasan(sesi.transkrip), SKEMA_RINGKASAN, "ringkasan_triase")
        try:
            ringkasan = RingkasanTriase.model_validate(isi)
        except ValidationError as galat:
            raise LlmTidakTersediaError("Ringkasan dari LLM tidak sesuai skema.") from galat
        sesi.selesaikan(ringkasan.model_dump(mode="json"), waktu)
        sesi.tambah_pesan(PERAN_EIR, PENUTUP, waktu)
        return self._balasan(sesi, PENUTUP)

    @staticmethod
    def _kueri(sesi: SesiEir) -> str:
        """Keluhan pertama ditambah jawaban terakhir, karena jawaban berikutnya sering pendek ("sejak kemarin")."""
        jawaban = [item["teks"] for item in sesi.transkrip if item["peran"] == PERAN_PENGISI]
        return " ".join(dict.fromkeys([jawaban[0], jawaban[-1]]))

    @staticmethod
    def _pertanyaan_cadangan(sesi: SesiEir, panduan: list[Panduan]) -> str:
        sudah: set[str] = {item["teks"] for item in sesi.transkrip if item["peran"] == PERAN_EIR}
        for p in panduan:
            for pertanyaan in p.pertanyaan:
                if pertanyaan not in sudah:
                    return pertanyaan
        return PERTANYAAN_UMUM
