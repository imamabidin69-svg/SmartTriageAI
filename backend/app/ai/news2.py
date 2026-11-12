"""National Early Warning Score 2 (Royal College of Physicians, 2017).

Skor dihitung dari tujuh parameter. Tabel poin di bawah mengikuti lembar NEWS2 resmi dengan skala SpO2 1
(skala 2 khusus pasien gagal napas hiperkapnia dan perlu ditetapkan dokter, jadi belum dipakai).
Pembagian level: total >= ambang kritis, >= ambang tinggi, lalu >= ambang sedang atau ada satu parameter
bernilai 3 (red score). Ambang bawaan 7, 5, dan 3 mengikuti respons klinis NEWS2.
"""

from dataclasses import dataclass
from decimal import Decimal

from app.ai.penjelasan import Faktor, format_angka
from app.models.enums import RiskLevel, TingkatKesadaran

POIN_MERAH = 3
SKOR_MAKSIMUM = 20


@dataclass(frozen=True)
class AmbangNews2:
    kritis: int
    tinggi: int
    sedang: int


@dataclass(frozen=True)
class HasilNews2:
    skor: int
    level: RiskLevel
    komponen: list[Faktor]

    @property
    def ada_poin_merah(self) -> bool:
        return any(faktor.kontribusi >= POIN_MERAH for faktor in self.komponen)


def poin_laju_napas(nilai: int) -> int:
    if nilai <= 8:
        return 3
    if nilai <= 11:
        return 1
    if nilai <= 20:
        return 0
    if nilai <= 24:
        return 2
    return 3


def poin_saturasi(nilai: Decimal) -> int:
    angka = float(nilai)
    if angka < 92:
        return 3
    if angka < 94:
        return 2
    if angka < 96:
        return 1
    return 0


def poin_sistolik(nilai: int) -> int:
    if nilai <= 90:
        return 3
    if nilai <= 100:
        return 2
    if nilai <= 110:
        return 1
    if nilai <= 219:
        return 0
    return 3


def poin_nadi(nilai: int) -> int:
    if nilai <= 40:
        return 3
    if nilai <= 50:
        return 1
    if nilai <= 90:
        return 0
    if nilai <= 110:
        return 1
    if nilai <= 130:
        return 2
    return 3


def poin_suhu(nilai: Decimal) -> int:
    angka = float(nilai)
    if angka <= 35.0:
        return 3
    if angka <= 36.0:
        return 1
    if angka <= 38.0:
        return 0
    if angka <= 39.0:
        return 1
    return 2


def poin_kesadaran(nilai: TingkatKesadaran) -> int:
    return 0 if nilai == TingkatKesadaran.SADAR_PENUH else 3


KETERANGAN_KESADARAN = {
    TingkatKesadaran.RESPONS_SUARA: "hanya respons terhadap suara",
    TingkatKesadaran.RESPONS_NYERI: "hanya respons terhadap nyeri",
    TingkatKesadaran.TIDAK_RESPONS: "tidak respons",
}


def hitung_news2(
    *,
    laju_napas: int,
    saturasi: Decimal,
    oksigen_tambahan: bool,
    td_sistolik: int,
    nadi: int,
    tingkat_kesadaran: TingkatKesadaran,
    suhu: Decimal,
    ambang: AmbangNews2,
) -> HasilNews2:
    """Menghitung skor dan level. Komponen hanya berisi parameter yang menyumbang poin, dari yang terbesar."""
    daftar = [
        ("laju_napas", f"Laju napas {laju_napas} x/menit", laju_napas, poin_laju_napas(laju_napas)),
        ("saturasi", f"Saturasi oksigen {format_angka(saturasi)}%", float(saturasi), poin_saturasi(saturasi)),
        ("oksigen_tambahan", "Mendapat oksigen tambahan", True, 2 if oksigen_tambahan else 0),
        ("td_sistolik", f"Tekanan darah sistolik {td_sistolik} mmHg", td_sistolik, poin_sistolik(td_sistolik)),
        ("nadi", f"Nadi {nadi} x/menit", nadi, poin_nadi(nadi)),
        (
            "tingkat_kesadaran",
            f"Kesadaran {tingkat_kesadaran.value} ({KETERANGAN_KESADARAN.get(tingkat_kesadaran, 'sadar penuh')})",
            tingkat_kesadaran.value,
            poin_kesadaran(tingkat_kesadaran),
        ),
        ("suhu", f"Suhu tubuh {format_angka(suhu)} °C", float(suhu), poin_suhu(suhu)),
    ]
    komponen = [
        Faktor(fitur=nama, label=label, nilai=nilai, kontribusi=poin, arah="naik")
        for nama, label, nilai, poin in daftar
        if poin > 0
    ]
    komponen.sort(key=lambda faktor: faktor.kontribusi, reverse=True)
    skor = int(sum(faktor.kontribusi for faktor in komponen))
    hasil = HasilNews2(skor=skor, level=RiskLevel.RENDAH, komponen=komponen)
    return HasilNews2(skor=skor, level=level_news2(skor, hasil.ada_poin_merah, ambang), komponen=komponen)


def level_news2(skor: int, ada_poin_merah: bool, ambang: AmbangNews2) -> RiskLevel:
    if skor >= ambang.kritis:
        return RiskLevel.KRITIS
    if skor >= ambang.tinggi:
        return RiskLevel.TINGGI
    if skor >= ambang.sedang or ada_poin_merah:
        return RiskLevel.SEDANG
    return RiskLevel.RENDAH
