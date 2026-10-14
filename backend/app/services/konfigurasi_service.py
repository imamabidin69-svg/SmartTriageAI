"""Konfigurasi triase: ambang aturan cadangan, batas waktu tunggu, dan ambang keyakinan (FR-05, FR-07).

Nilainya dibaca lewat CacheKonfigurasi yang menyimpan salinan di memori proses selama 60 detik
(Desain baris 380). Setelah PATCH, cache di worker yang memproses perubahan langsung dikosongkan;
worker Gunicorn lain menyesuaikan paling lambat setelah masa cache habis.
"""

import time
from collections.abc import Callable
from dataclasses import dataclass, fields
from decimal import Decimal

from flask import current_app
from sqlalchemy import select

from app.ai.klasifikasi import AmbangAturan
from app.ai.registry import ModelRegistry
from app.extensions import db
from app.models import Konfigurasi, Pengguna
from app.models.enums import AksiAudit, RiskLevel
from app.services.audit_logger import AuditLogger
from app.utils.errors import PenerjemahPesan, ValidasiGagalError
from app.utils.schemas import KonfigurasiPatch

ID_KONFIGURASI = 1


@dataclass(frozen=True)
class NilaiKonfigurasi:
    """Salinan baris konfigurasi yang terlepas dari sesi SQLAlchemy, aman disimpan di cache."""

    versi_model: str
    ambang_kritis: int
    ambang_tinggi: int
    ambang_sedang: int
    batas_tunggu_tinggi: int
    batas_tunggu_sedang: int
    batas_tunggu_rendah: int
    ambang_keyakinan: Decimal

    @classmethod
    def dari_model(cls, baris: Konfigurasi) -> "NilaiKonfigurasi":
        return cls(**{kolom.name: getattr(baris, kolom.name) for kolom in fields(cls)})

    @property
    def ambang_aturan(self) -> AmbangAturan:
        return AmbangAturan(kritis=self.ambang_kritis, tinggi=self.ambang_tinggi, sedang=self.ambang_sedang)

    def batas_tunggu(self, level: RiskLevel) -> int | None:
        """Batas tunggu dalam menit. Kritis tidak punya batas karena harus segera ditangani."""
        return {
            RiskLevel.TINGGI: self.batas_tunggu_tinggi,
            RiskLevel.SEDANG: self.batas_tunggu_sedang,
            RiskLevel.RENDAH: self.batas_tunggu_rendah,
        }.get(level)


class KonfigurasiTidakAdaError(RuntimeError):
    """Baris konfigurasi hilang; seharusnya selalu disisipkan migrasi awal."""


class CacheKonfigurasi:
    def __init__(self, ttl_detik: float, jam: Callable[[], float] = time.monotonic) -> None:
        self.ttl_detik = ttl_detik
        self.jam = jam
        self._nilai: NilaiKonfigurasi | None = None
        self._kedaluwarsa = 0.0

    def ambil(self) -> NilaiKonfigurasi:
        sekarang = self.jam()
        if self._nilai is None or sekarang >= self._kedaluwarsa:
            baris = db.session.get(Konfigurasi, ID_KONFIGURASI)
            if baris is None:
                raise KonfigurasiTidakAdaError("Baris konfigurasi tidak ditemukan. Jalankan flask db upgrade.")
            self._nilai = NilaiKonfigurasi.dari_model(baris)
            self._kedaluwarsa = sekarang + self.ttl_detik
        return self._nilai

    def kosongkan(self) -> None:
        self._nilai = None


def cache_konfigurasi() -> CacheKonfigurasi:
    return current_app.extensions["cache_konfigurasi"]


# Pasangan (lebih besar, lebih kecil) yang harus berurutan, sama dengan CHECK di basis data.
URUTAN_AMBANG = (("ambang_kritis", "ambang_tinggi"), ("ambang_tinggi", "ambang_sedang"))
URUTAN_BATAS_TUNGGU = (("batas_tunggu_sedang", "batas_tunggu_tinggi"), ("batas_tunggu_rendah", "batas_tunggu_sedang"))


class KonfigurasiService:
    def __init__(self, registry: ModelRegistry, cache: CacheKonfigurasi) -> None:
        self.registry = registry
        self.cache = cache

    def ambil(self) -> NilaiKonfigurasi:
        return self.cache.ambil()

    def ubah(self, data: KonfigurasiPatch, admin: Pengguna) -> NilaiKonfigurasi:
        baris = db.session.scalar(
            select(Konfigurasi).where(Konfigurasi.id_konfigurasi == ID_KONFIGURASI).with_for_update()
        )
        if baris is None:
            raise KonfigurasiTidakAdaError("Baris konfigurasi tidak ditemukan. Jalankan flask db upgrade.")

        baru = {nama: getattr(data, nama) for nama in data.model_fields_set}
        gabungan = {kolom.name: baru.get(kolom.name, getattr(baris, kolom.name)) for kolom in fields(NilaiKonfigurasi)}
        self._periksa(baru, gabungan)

        perubahan = [(nama, getattr(baris, nama), isi) for nama, isi in baru.items() if getattr(baris, nama) != isi]
        for nama, _lama, nilai in perubahan:
            setattr(baris, nama, nilai)
        if perubahan:
            urutan = [kolom.name for kolom in fields(NilaiKonfigurasi)]
            perubahan.sort(key=lambda item: urutan.index(item[0]))
            catatan = "; ".join(f"{nama}: {lama} -> {nilai}" for nama, lama, nilai in perubahan)
            AuditLogger().catat(AksiAudit.UBAH_KONFIGURASI, admin, catatan=catatan)
        db.session.commit()
        self.cache.kosongkan()
        return NilaiKonfigurasi.dari_model(baris)

    def _periksa(self, baru: dict, gabungan: dict) -> None:
        label = PenerjemahPesan.LABEL
        galat: list[dict[str, str]] = []

        for besar, kecil in URUTAN_AMBANG:
            if gabungan[besar] <= gabungan[kecil]:
                if besar in baru:
                    pesan = f"{label[besar]} harus lebih besar dari {label[kecil].lower()} ({gabungan[kecil]})."
                    galat.append({"field": besar, "pesan": pesan})
                else:
                    pesan = f"{label[kecil]} harus lebih kecil dari {label[besar].lower()} ({gabungan[besar]})."
                    galat.append({"field": kecil, "pesan": pesan})

        for besar, kecil in URUTAN_BATAS_TUNGGU:
            if gabungan[besar] < gabungan[kecil]:
                if besar in baru:
                    pesan = (
                        f"{label[besar]} tidak boleh lebih kecil dari {label[kecil].lower()} ({gabungan[kecil]} menit)."
                    )
                    galat.append({"field": besar, "pesan": pesan})
                else:
                    pesan = (
                        f"{label[kecil]} tidak boleh lebih besar dari {label[besar].lower()} ({gabungan[besar]} menit)."
                    )
                    galat.append({"field": kecil, "pesan": pesan})

        if "versi_model" in baru and baru["versi_model"] != self.registry.versi_model:
            if self.registry.versi_model is None:
                pesan = "Model triase belum dimuat, jadi versi model belum bisa diubah."
            else:
                pesan = f"Versi model harus sama dengan model yang sedang dimuat ({self.registry.versi_model})."
            galat.append({"field": "versi_model", "pesan": pesan})

        if galat:
            # Satu pesan per field cukup; ambang tinggi bisa melanggar dua pasangan sekaligus.
            unik = {item["field"]: item for item in reversed(galat)}
            raise ValidasiGagalError([item for item in galat if unik[item["field"]] is item])
