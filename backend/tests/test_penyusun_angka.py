"""PenyusunAngka dan PemetaKolom (FR-04, Desain 7.3, keputusan P2 dan P4)."""

from decimal import Decimal

import pytest

from app.ai.pembaca_layar import Digit, digit_dari_baris
from app.ai.penyusun_angka import Angka, PemetaKolom, PenyusunAngka
from app.models.enums import JenisAlat


def _teks(angka: list[Angka]) -> list[str]:
    return [a.teks for a in angka]


def test_baris_disusun_dari_atas_ke_bawah_lalu_kiri_ke_kanan():
    digit = digit_dari_baris(["128", "84", "76"])
    # Urutan masukan diacak supaya penyusun yang benar-benar mengurutkan.
    acak = [digit[4], digit[0], digit[6], digit[2], digit[3], digit[5], digit[1]]
    assert _teks(PenyusunAngka().susun(acak)) == ["128", "84", "76"]


def test_digit_sedikit_miring_tetap_satu_baris():
    # Foto miring: tiap digit turun 15 piksel dari digit di kirinya (tinggi digit 80).
    digit = [Digit(n, 0.9, 80 + i * 50, 60 + i * 15, 120 + i * 50, 140 + i * 15) for i, n in enumerate([1, 3, 5])]
    assert _teks(PenyusunAngka().susun(digit)) == ["135"]


def test_dua_angka_berjauhan_dalam_satu_baris_dipisah():
    kiri = [Digit(9, 0.9, 80, 60, 120, 140), Digit(7, 0.9, 130, 60, 170, 140)]
    kanan = [Digit(8, 0.9, 300, 60, 340, 140), Digit(2, 0.9, 350, 60, 390, 140)]
    assert _teks(PenyusunAngka().susun(kanan + kiri)) == ["97", "82"]


def test_keyakinan_angka_adalah_digit_terendah():
    digit = [Digit(1, 0.99, 80, 60, 120, 140), Digit(2, 0.61, 130, 60, 170, 140), Digit(8, 0.95, 180, 60, 220, 140)]
    [angka] = PenyusunAngka().susun(digit)
    assert angka.keyakinan == 0.61


def test_tanpa_digit():
    assert PenyusunAngka().susun([]) == []


def _angka(*teks: str, keyakinan: float = 0.97) -> list[Angka]:
    return [Angka(tuple(int(c) for c in t), keyakinan) for t in teks]


@pytest.mark.parametrize(
    ("jenis", "angka", "hasil"),
    [
        (JenisAlat.TENSIMETER, ("128", "84", "76"), {"td_sistolik": 128, "td_diastolik": 84, "nadi": 76}),
        (JenisAlat.OKSIMETER, ("97", "82"), {"saturasi": 97, "nadi": 82}),
        (JenisAlat.TERMOMETER, ("368",), {"suhu": Decimal("36.8")}),
        (JenisAlat.TERMOMETER, ("37",), {"suhu": Decimal("37")}),
        (JenisAlat.TERMOMETER, ("3685",), {}),
        # Keputusan P2b: bedside monitor dikosongkan sampai jenis monitor di dataset diketahui.
        (JenisAlat.BEDSIDE_MONITOR, ("82", "97", "128", "84", "18", "368"), {}),
    ],
)
def test_pemetaan_per_alat(jenis, angka, hasil):
    terpetakan = PemetaKolom().petakan(_angka(*angka), jenis)
    assert {k: v.nilai for k, v in terpetakan.items()} == hasil


@pytest.mark.parametrize("angka", [("128", "84"), ("10", "30", "128", "84", "76")])
def test_jumlah_angka_tidak_cocok_semua_kolom_kosong(angka):
    # Angka tambahan seperti jam atau nomor memori membuat urutan baris tidak bisa dipercaya.
    assert PemetaKolom().petakan(_angka(*angka), JenisAlat.TENSIMETER) == {}


def test_keyakinan_ikut_terbawa():
    terpetakan = PemetaKolom().petakan(_angka("97", "82", keyakinan=0.7), JenisAlat.OKSIMETER)
    assert {v.keyakinan for v in terpetakan.values()} == {0.7}
