"""PenyusunAngka dan PemetaKolom (FR-04, Desain 7.3).

PenyusunAngka mengelompokkan kotak digit per baris berdasarkan posisi vertikal, mengurutkannya dari
kiri ke kanan, lalu memisahkan angka yang berjauhan dalam satu baris. PemetaKolom memetakan angka
ke kolom tanda vital menurut jenis alat (keputusan P2).
"""

from dataclasses import dataclass
from decimal import Decimal
from statistics import median

from app.ai.pembaca_layar import Digit
from app.models.enums import JenisAlat

# Dua digit masuk baris yang sama bila selisih titik tengah vertikalnya paling banyak setengah tinggi digit.
TOLERANSI_BARIS = 0.5
# Celah horizontal yang lebih lebar dari 0,8 kali lebar digit memisahkan dua angka dalam satu baris.
CELAH_ANTAR_ANGKA = 0.8


@dataclass(frozen=True)
class Angka:
    digit: tuple[int, ...]
    keyakinan: float

    @property
    def teks(self) -> str:
        return "".join(str(d) for d in self.digit)


class PenyusunAngka:
    def susun(self, digit: list[Digit]) -> list[Angka]:
        """Angka diurutkan dari baris paling atas, lalu dari kiri ke kanan."""
        if not digit:
            return []
        tinggi_median = median(d.tinggi for d in digit)
        lebar_median = median(d.lebar for d in digit)

        baris: list[list[Digit]] = []
        for d in sorted(digit, key=lambda d: d.tengah_y):
            if baris and abs(d.tengah_y - median(x.tengah_y for x in baris[-1])) <= TOLERANSI_BARIS * tinggi_median:
                baris[-1].append(d)
            else:
                baris.append([d])

        hasil: list[Angka] = []
        for isi in baris:
            kelompok: list[list[Digit]] = []
            for d in sorted(isi, key=lambda d: d.x1):
                if kelompok and d.x1 - kelompok[-1][-1].x2 <= CELAH_ANTAR_ANGKA * lebar_median:
                    kelompok[-1].append(d)
                else:
                    kelompok.append([d])
            # Keyakinan sebuah angka adalah keyakinan terendah dari digitnya (keputusan P4).
            hasil += [Angka(tuple(x.nilai for x in k), min(x.keyakinan for x in k)) for k in kelompok]
        return hasil


# Urutan kolom per jenis alat. Bedside monitor dikosongkan dulu karena tata letaknya berbeda-beda
# antar merek, sampai jenis monitor di dataset diketahui (keputusan P2b).
KOLOM_ALAT: dict[JenisAlat, tuple[str, ...]] = {
    JenisAlat.TENSIMETER: ("td_sistolik", "td_diastolik", "nadi"),
    JenisAlat.OKSIMETER: ("saturasi", "nadi"),
    JenisAlat.TERMOMETER: ("suhu",),
    JenisAlat.BEDSIDE_MONITOR: (),
}
# Kolom yang ditampilkan di respons untuk setiap alat, termasuk yang belum bisa dibaca.
KOLOM_TAMPIL: dict[JenisAlat, tuple[str, ...]] = {
    **KOLOM_ALAT,
    JenisAlat.BEDSIDE_MONITOR: ("td_sistolik", "td_diastolik", "nadi", "laju_napas", "suhu", "saturasi"),
}


@dataclass(frozen=True)
class NilaiKolom:
    nilai: int | Decimal
    keyakinan: float


class PemetaKolom:
    def petakan(self, angka: list[Angka], jenis_alat: JenisAlat) -> dict[str, NilaiKolom]:
        """Jumlah angka harus sama persis dengan jumlah kolom alat.

        Bila ada angka tambahan (misalnya jam atau nomor memori) atau ada yang kurang, urutan baris tidak
        bisa dipercaya, sehingga semua kolom dikosongkan untuk diisi manual.
        """
        kolom = KOLOM_ALAT[jenis_alat]
        if not kolom or len(angka) != len(kolom):
            return {}
        hasil = {}
        for nama, a in zip(kolom, angka, strict=True):
            nilai = self._nilai(nama, a)
            if nilai is not None:
                hasil[nama] = NilaiKolom(nilai, a.keyakinan)
        return hasil

    @staticmethod
    def _nilai(kolom: str, angka: Angka) -> int | Decimal | None:
        bulat = int(angka.teks)
        if kolom != "suhu":
            return bulat
        # Model hanya mengenali digit 0-9 tanpa titik desimal: "368" dibaca 36,8 dan "37" dibaca 37.
        if len(angka.digit) == 3:
            return Decimal(bulat) / 10
        if len(angka.digit) == 2:
            return Decimal(bulat)
        return None
