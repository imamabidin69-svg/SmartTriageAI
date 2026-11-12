"""DetektorInformasiPenting untuk keluarga pasien ICU (FR-08, NFR-04, SKPL TC-14 disesuaikan).

Setiap jenis informasi punya beberapa kalimat positif. Kalimat negatif memastikan cerita biasa dan
penyangkalan seperti "tidak ada alergi obat" tidak ditandai, karena label yang salah membingungkan perawat.
"""

import pytest

from app.ai.eir.informasi_penting import POLA_INFORMASI_PENTING, DetektorInformasiPenting, normalisasi

SKENARIO = {
    "alergi_obat": [
        "Bapak alergi amoxicillin",
        "ibu ada alergi obat antibiotik",
        "alerginya sama paracetamol, langsung bengkak",
        "pernah disuntik obat langsung sesak",
        "elergi obat asam mefenamat",
    ],
    "alergi_lain": ["alergi udang dan kepiting", "alergi makanan laut", "alergi plester"],
    "pengencer_darah": ["minum warfarin tiap malam", "rutin minum clopidogrel", "pakai obat pengencer darah"],
    "insulin": ["suntik insulin dua kali sehari", "pakai lantus malam hari"],
    "kehamilan": ["ibu sedang hamil lima bulan", "baru melahirkan seminggu lalu", "habis keguguran bulan lalu"],
    "alat_implan": ["bapak pakai alat pacu jantung", "sudah pasang ring jantung", "ada pen di kaki kiri"],
    "masalah_pembiusan": ["waktu dibius operasi dulu lama sekali sadarnya", "pernah ada reaksi waktu dibius"],
    "penyakit_menular": ["pernah sakit TBC", "ada riwayat hepatitis B", "positif HIV"],
    "keinginan_pasien": ["bapak tidak mau dipasang ventilator", "ibu jangan diresusitasi katanya", "ada DNR"],
}

KALIMAT_BIASA = [
    "tidak ada alergi obat",
    "setahu saya tidak alergi makanan",
    "tidak pernah minum pengencer darah",
    "ibu tidak hamil",
    "bapak punya darah tinggi dan kencing manis",
    "awalnya sesak lalu dibawa ke IGD",
    "terakhir minum obat kemarin pagi",
    "pernah operasi usus buntu",
    "minum amlodipin setiap pagi",
]

DETEKTOR = DetektorInformasiPenting()


@pytest.mark.parametrize(
    ("kode", "kalimat"),
    [(kode, kalimat) for kode, daftar in SKENARIO.items() for kalimat in daftar],
)
def test_informasi_penting_tertangkap(kode, kalimat):
    assert kode in [info.kode for info in DETEKTOR.periksa(kalimat)]


@pytest.mark.parametrize("kalimat", KALIMAT_BIASA)
def test_kalimat_biasa_dan_penyangkalan_tidak_ditandai(kalimat):
    assert DETEKTOR.periksa(kalimat) == []


def test_satu_pesan_bisa_berisi_beberapa_informasi_tanpa_duplikat():
    hasil = DETEKTOR.periksa("Bapak alergi penisilin. Dia juga minum warfarin, dan alergi amoxicillin juga")
    assert [info.kode for info in hasil] == ["alergi_obat", "pengencer_darah"]
    assert [info.label for info in hasil] == ["Alergi obat", "Memakai obat pengencer darah"]


def test_penyangkalan_hanya_berlaku_di_klausa_sendiri():
    hasil = DETEKTOR.periksa("Tidak ada alergi makanan, tapi alergi obat sulfa")
    assert [info.kode for info in hasil] == ["alergi_obat"]


def test_semua_kode_unik_dan_punya_skenario():
    kode = [k for k, *_ in POLA_INFORMASI_PENTING]
    assert len(kode) == len(set(kode))
    assert set(kode) == set(SKENARIO)


@pytest.mark.parametrize(
    ("teks", "hasil"),
    [
        ("Gak ada ALERGI!", "tidak ada alergi"),
        ("obatnya warfarin", "obat warfarin"),
        ("alerginya amoksisilin", "alergi amoxicillin"),
    ],
)
def test_normalisasi(teks, hasil):
    assert normalisasi(teks) == hasil
