"""Pemindaian layar alat tanda vital (FR-04, Desain 2.4 dan Gambar 2.10-2.12).

Foto hanya diproses di memori lalu dibuang. Kolom hanya diisi bila keyakinan angkanya mencapai ambang
dari tabel konfigurasi dan nilainya masuk rentang yang mungkin dicatat; selebihnya dibiarkan kosong untuk
diisi manual. Endpoint ini tidak mengubah triase, karena nilai baru dipakai setelah perawat mengirim form.
"""

import io
import logging
from dataclasses import dataclass
from decimal import Decimal

from PIL import Image, ImageOps, UnidentifiedImageError
from werkzeug.datastructures import FileStorage

from app.ai.pembaca_layar import Digit, PembacaLayar
from app.ai.penyusun_angka import KOLOM_TAMPIL, NilaiKolom, PemetaKolom, PenyusunAngka
from app.extensions import db
from app.models import PemindaianAlat, Pengguna
from app.models.enums import JenisAlat
from app.services.konfigurasi_service import CacheKonfigurasi
from app.services.triase_service import BATAS_VITAL
from app.utils.errors import ValidasiGagalError

logger = logging.getLogger(__name__)

FORMAT_DIIZINKAN = ("JPEG", "PNG")
# Gambar raksasa ditolak sebelum didekode supaya server tidak kehabisan memori (keputusan P8).
PIKSEL_MAKSIMUM = 40_000_000
UKURAN_PROSES = 640
# Rentang wajar memakai batas salah ketik dari prototipe, bukan ambang klinis, supaya nilai abnormal
# yang benar (misalnya saturasi 85%) tetap terbaca (keputusan P3).
RENTANG_WAJAR = {b.field: (b.salah_ketik_bawah, b.salah_ketik_atas) for b in BATAS_VITAL}


@dataclass(frozen=True)
class HasilBaca:
    pemindaian: PemindaianAlat
    nilai: dict[str, float | None]
    keyakinan: dict[str, float | None]
    kolom_kosong: list[str]
    pembaca_tersedia: bool


def _galat_foto(pesan: str) -> ValidasiGagalError:
    return ValidasiGagalError([{"field": "berkas", "pesan": pesan}])


def _angka_json(nilai: int | Decimal) -> int | float:
    return float(nilai) if isinstance(nilai, Decimal) else nilai


class PemindaianService:
    def __init__(self, pembaca: PembacaLayar | None, cache: CacheKonfigurasi, ukuran_maks: int) -> None:
        self.pembaca = pembaca
        self.cache = cache
        self.ukuran_maks = ukuran_maks

    def pindai(self, berkas: FileStorage, jenis_alat: JenisAlat, perawat: Pengguna) -> HasilBaca:
        gambar = self._buka_foto(berkas)
        digit = self._deteksi(gambar, jenis_alat)
        del gambar  # foto tidak disimpan di mana pun (Desain Gambar 2.10)

        terbaca = PemetaKolom().petakan(PenyusunAngka().susun(digit), jenis_alat)
        ambang = float(self.cache.ambil().ambang_keyakinan)
        terisi = {kolom: n for kolom, n in terbaca.items() if self._layak(kolom, n, ambang)}

        pemindaian = PemindaianAlat(
            dipindai_oleh=perawat.id_pengguna,
            jenis_alat=jenis_alat,
            nilai_terbaca={kolom: _angka_json(n.nilai) for kolom, n in terisi.items()},
            keyakinan=self._keyakinan_baris(terisi, digit),
        )
        try:
            db.session.add(pemindaian)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        db.session.refresh(pemindaian)

        kolom = KOLOM_TAMPIL[jenis_alat]
        return HasilBaca(
            pemindaian=pemindaian,
            nilai={k: (_angka_json(terisi[k].nilai) if k in terisi else None) for k in kolom},
            keyakinan={k: (round(terbaca[k].keyakinan, 3) if k in terbaca else None) for k in kolom},
            kolom_kosong=[k for k in kolom if k not in terisi],
            pembaca_tersedia=self.pembaca is not None,
        )

    def _buka_foto(self, berkas: FileStorage) -> Image.Image:
        if not isinstance(berkas, FileStorage):
            raise _galat_foto("Foto harus dikirim sebagai berkas.")
        data = berkas.stream.read(self.ukuran_maks + 1)
        if not data:
            raise _galat_foto("Foto kosong.")
        if len(data) > self.ukuran_maks:
            raise _galat_foto(f"Ukuran foto maksimal {self.ukuran_maks // (1024 * 1024)} MB.")
        try:
            gambar = Image.open(io.BytesIO(data))
            if gambar.format not in FORMAT_DIIZINKAN:
                raise _galat_foto("Foto harus berformat JPEG atau PNG.")
            if gambar.width * gambar.height > PIKSEL_MAKSIMUM:
                raise _galat_foto("Resolusi foto terlalu besar.")
            gambar.load()
            # Foto ponsel sering menyimpan arah putar di EXIF; diluruskan dulu supaya baris digit benar.
            gambar = ImageOps.exif_transpose(gambar).convert("RGB")
        except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError) as galat:
            raise _galat_foto("Berkas bukan foto JPEG atau PNG yang valid.") from galat
        gambar.thumbnail((UKURAN_PROSES, UKURAN_PROSES))
        return gambar

    def _deteksi(self, gambar: Image.Image, jenis_alat: JenisAlat) -> list[Digit]:
        if self.pembaca is None:
            return []
        try:
            return self.pembaca.deteksi(gambar, jenis_alat)
        except Exception:
            # Pembaca yang gagal tidak menggagalkan pemindaian; kolom diisi manual (Desain baris 396).
            logger.exception("Pembaca layar gagal memproses foto %s.", jenis_alat.value)
            return []

    @staticmethod
    def _layak(kolom: str, nilai: NilaiKolom, ambang: float) -> bool:
        bawah, atas = RENTANG_WAJAR[kolom]
        return nilai.keyakinan >= ambang and bawah <= nilai.nilai <= atas

    @staticmethod
    def _keyakinan_baris(terisi: dict[str, NilaiKolom], digit: list[Digit]) -> Decimal:
        """Keputusan P1: keyakinan terendah dari kolom yang terisi. Bila tidak ada yang terisi, keyakinan
        digit tertinggi yang terdeteksi, atau 0 bila tidak ada digit sama sekali."""
        terendah = min((n.keyakinan for n in terisi.values()), default=None)
        nilai = terendah if terendah is not None else max((d.keyakinan for d in digit), default=0.0)
        return Decimal(str(round(min(max(nilai, 0.0), 1.0), 3)))
