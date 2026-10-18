"""Alur Eir untuk pasien zona hijau dan keluarganya (FR-08, Desain 2.8 dan Gambar 2.22-2.24).

Perawat membuat tautan untuk kunjungan yang risk level terakhirnya rendah. Pasien atau keluarga membuka
tautan, memberi persetujuan, lalu menjawab pertanyaan. Rekaman suara dan teks hanya diproses di memori;
yang disimpan hanya transkrip di sesi_eir.
"""

import math
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

from flask import current_app
from limits import parse
from sqlalchemy import select
from werkzeug.datastructures import FileStorage

from app.ai.eir.agen import Balasan, EirAgent
from app.ai.eir.llm import LlmTidakTersediaError
from app.ai.eir.prompt import PembersihIdentitas
from app.ai.eir.tanda_bahaya import RedFlagDetector
from app.ai.eir.tautan import TautanEir, TokenSesiEir
from app.ai.registry import ModelRegistry
from app.extensions import db, limiter
from app.models import Kunjungan, SesiEir, Triase
from app.models.enums import PengisiEir, RiskLevel, StatusKunjungan
from app.utils.errors import (
    KonflikError,
    LayananTidakTersediaError,
    TerlaluBanyakPercobaanError,
    TidakDitemukanError,
    ValidasiGagalError,
)
from app.utils.waktu import sekarang

PESAN_TIDAK_TERSEDIA = "Eir sedang tidak dapat menjawab. Silakan sampaikan keluhan langsung ke perawat."


@dataclass(frozen=True)
class TautanDibuat:
    token: str
    kedaluwarsa: datetime


@dataclass(frozen=True)
class SesiDibuka:
    sesi: SesiEir
    token_sesi: str
    kedaluwarsa: datetime
    pesan: str


def jenis_audio(data: bytes) -> str | None:
    """Format rekaman dikenali dari isi berkas, bukan dari nama atau Content-Type kiriman klien."""
    if data[:4] == b"\x1aE\xdf\xa3":
        return "webm"
    if data[:4] == b"OggS":
        return "ogg"
    if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        return "wav"
    if data[4:8] == b"ftyp":
        return "m4a"
    if data[:3] == b"ID3" or (len(data) > 1 and data[0] == 0xFF and data[1] & 0xE0 == 0xE0):
        return "mp3"
    return None


def _galat_suara(pesan: str) -> ValidasiGagalError:
    return ValidasiGagalError([{"field": "berkas", "pesan": pesan}])


class EirService:
    def __init__(self, registry: ModelRegistry) -> None:
        config = current_app.config
        self.umur = int(config["UMUR_TOKEN_EIR_DETIK"])
        self.tautan = TautanEir(config["SECRET_KEY"], self.umur)
        self.token_sesi = TokenSesiEir(config["SECRET_KEY"], self.umur)
        self.agen = EirAgent(
            RedFlagDetector(),
            registry.retriever,
            registry.llm,
            int(config["EIR_MIN_JAWABAN"]),
            int(config["EIR_MAKS_JAWABAN"]),
        )
        self.llm = registry.llm

    # ------------------------------------------------------------ untuk perawat

    def buat_tautan(self, id_kunjungan: uuid.UUID) -> TautanDibuat:
        self._kunjungan_layak(id_kunjungan)
        return TautanDibuat(self.tautan.buat(id_kunjungan), sekarang() + timedelta(seconds=self.umur))

    @staticmethod
    def sesi_terakhir(id_kunjungan: uuid.UUID) -> SesiEir:
        if db.session.get(Kunjungan, id_kunjungan) is None:
            raise TidakDitemukanError("Kunjungan tidak ditemukan.")
        sesi = db.session.scalar(
            select(SesiEir)
            .where(SesiEir.id_kunjungan == id_kunjungan)
            .order_by(SesiEir.waktu_persetujuan.desc(), SesiEir.id_sesi.desc())
            .limit(1)
        )
        if sesi is None:
            raise TidakDitemukanError("Kunjungan ini belum punya sesi Eir.")
        return sesi

    # ------------------------------------------------------------ untuk pasien atau keluarga

    def buka_sesi(self, token: str, pengisi: PengisiEir) -> SesiDibuka:
        id_kunjungan = self.tautan.baca(token)
        waktu = sekarang()
        try:
            # FOR SHARE: status kunjungan tidak boleh berubah di antara pemeriksaan dan pembuatan sesi.
            self._kunjungan_layak(id_kunjungan, kunci=True)
            sesi = SesiEir(id_kunjungan=id_kunjungan, pengisi=pengisi, waktu_persetujuan=waktu, transkrip=[])
            pesan = self.agen.mulai(sesi, waktu)
            db.session.add(sesi)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        db.session.refresh(sesi)
        return SesiDibuka(sesi, self.token_sesi.buat(sesi.id_sesi), waktu + timedelta(seconds=self.umur), pesan)

    # Token sesi sudah diperiksa dekorator token_sesi_wajib di routes/eir.py sebelum method di bawah dipanggil.

    def kirim_pesan(self, id_sesi: uuid.UUID, teks: str) -> Balasan:
        self._batasi_pesan(id_sesi)
        return self._proses(id_sesi, teks)

    def kirim_suara(self, id_sesi: uuid.UUID, berkas: FileStorage) -> tuple[Balasan, str]:
        """Rekaman diubah ke teks lalu diproses seperti pesan biasa. Rekaman tidak pernah disimpan."""
        self._batasi_pesan(id_sesi)
        # Status diperiksa dulu supaya rekaman untuk sesi yang sudah berakhir tidak dikirim ke Groq.
        self._sesi_berjalan(self._ambil_sesi(id_sesi))
        db.session.rollback()
        audio, format_audio = self._baca_audio(berkas)
        if self.llm is None:
            raise LayananTidakTersediaError(PESAN_TIDAK_TERSEDIA)
        try:
            teks = self.llm.transkripsi(audio, f"rekaman.{format_audio}")
        except LlmTidakTersediaError as galat:
            raise LayananTidakTersediaError(PESAN_TIDAK_TERSEDIA) from galat
        finally:
            del audio
        if not teks:
            raise _galat_suara("Suara tidak terdengar jelas. Coba rekam ulang atau ketik jawabannya.")
        return self._proses(id_sesi, teks[:1000]), teks[:1000]

    def selesai(self, id_sesi: uuid.UUID) -> Balasan:
        sesi = self._ambil_sesi(id_sesi, kunci=True)
        try:
            self._sesi_berjalan(sesi)
            if sesi.jumlah_jawaban < self.agen.min_jawaban:
                raise KonflikError(
                    f"Jawab minimal {self.agen.min_jawaban} pertanyaan dulu sebelum menyelesaikan.",
                    ekstra={"jumlah_jawaban": sesi.jumlah_jawaban},
                )
            balasan = self.agen.ringkas(sesi, self._pembersih(sesi), sekarang())
            db.session.commit()
        except LlmTidakTersediaError as galat:
            db.session.rollback()
            raise LayananTidakTersediaError(PESAN_TIDAK_TERSEDIA) from galat
        except Exception:
            db.session.rollback()
            raise
        return balasan

    # ------------------------------------------------------------ bantuan

    def _proses(self, id_sesi: uuid.UUID, teks: str) -> Balasan:
        # FOR UPDATE: dua pesan dari sesi yang sama diproses bergantian supaya transkrip tidak saling menimpa.
        sesi = self._ambil_sesi(id_sesi, kunci=True)
        try:
            self._sesi_berjalan(sesi)
            if sesi.jumlah_jawaban >= self.agen.maks_jawaban:
                raise KonflikError("Jawaban sudah cukup. Tekan Selesai untuk mengirim ringkasan ke perawat.")
            balasan = self.agen.proses(sesi, teks, self._pembersih(sesi), sekarang())
            db.session.commit()
        except LlmTidakTersediaError as galat:
            # Keputusan E3: jawaban pasien tetap tersimpan dan sesi tetap berjalan.
            db.session.commit()
            raise LayananTidakTersediaError(PESAN_TIDAK_TERSEDIA) from galat
        except Exception:
            db.session.rollback()
            raise
        return balasan

    @staticmethod
    def _batasi_pesan(id_sesi: uuid.UUID) -> None:
        """Maksimal 20 pesan per menit per sesi untuk menahan biaya dan penyalahgunaan (Desain 7.2)."""
        if not limiter.enabled:
            return
        item = parse(current_app.config["BATAS_PESAN_EIR"])
        kunci = f"pesan-eir:{id_sesi}"
        if not limiter.limiter.hit(item, kunci):
            reset = limiter.limiter.get_window_stats(item, kunci).reset_time
            raise TerlaluBanyakPercobaanError(
                "Pesan dikirim terlalu cepat. Tunggu sebentar lalu kirim lagi.", max(1, math.ceil(reset - time.time()))
            )

    @staticmethod
    def _ambil_sesi(id_sesi: uuid.UUID, kunci: bool = False) -> SesiEir:
        kueri = select(SesiEir).where(SesiEir.id_sesi == id_sesi)
        if kunci:
            kueri = kueri.with_for_update().execution_options(populate_existing=True)
        sesi = db.session.scalar(kueri)
        if sesi is None:
            raise TidakDitemukanError("Sesi Eir tidak ditemukan.")
        return sesi

    @staticmethod
    def _sesi_berjalan(sesi: SesiEir) -> None:
        if not sesi.berjalan:
            raise KonflikError("Sesi Eir sudah berakhir.", ekstra={"status": sesi.status.value})
        if sesi.kunjungan.status != StatusKunjungan.MENUNGGU:
            raise KonflikError("Pasien sudah dipanggil untuk diperiksa. Sampaikan keluhan langsung ke petugas.")

    @staticmethod
    def _pembersih(sesi: SesiEir) -> PembersihIdentitas:
        pasien = sesi.kunjungan.pasien
        return PembersihIdentitas(pasien.nama, pasien.nik, pasien.no_telepon)

    @staticmethod
    def _kunjungan_layak(id_kunjungan: uuid.UUID, kunci: bool = False) -> Kunjungan:
        """Eir khusus kunjungan yang masih menunggu dan risk level terakhirnya rendah (Desain 2.8)."""
        kueri = select(Kunjungan).where(Kunjungan.id_kunjungan == id_kunjungan)
        if kunci:
            kueri = kueri.with_for_update(read=True)
        kunjungan = db.session.scalar(kueri)
        if kunjungan is None:
            raise TidakDitemukanError("Kunjungan tidak ditemukan.")
        if kunjungan.status != StatusKunjungan.MENUNGGU:
            raise KonflikError("Eir hanya untuk pasien yang masih menunggu.")
        level = db.session.scalar(
            select(Triase.risk_level)
            .where(Triase.id_kunjungan == id_kunjungan)
            .order_by(Triase.waktu_triase.desc(), Triase.id_triase.desc())
            .limit(1)
        )
        if level is None:
            raise KonflikError("Pasien belum ditriase.")
        if level != RiskLevel.RENDAH:
            raise KonflikError("Eir hanya untuk pasien dengan risk level terakhir rendah (zona hijau).")
        return kunjungan

    @staticmethod
    def _baca_audio(berkas: FileStorage) -> tuple[bytes, str]:
        if not isinstance(berkas, FileStorage):
            raise _galat_suara("Rekaman harus dikirim sebagai berkas.")
        batas = int(current_app.config["UKURAN_MAKS_SUARA"])
        data = berkas.stream.read(batas + 1)
        if not data:
            raise _galat_suara("Rekaman kosong.")
        if len(data) > batas:
            raise _galat_suara(f"Ukuran rekaman maksimal {batas // (1024 * 1024)} MB.")
        format_audio = jenis_audio(data)
        if format_audio is None:
            raise _galat_suara("Rekaman harus berformat webm, ogg, mp3, m4a, atau wav.")
        return data, format_audio
