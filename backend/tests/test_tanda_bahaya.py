"""RedFlagDetector (FR-08, NFR-03, NFR-04, SKPL TC-14).

NFR-04 meminta seluruh skenario uji tanda bahaya tertangkap, jadi setiap kelompok punya beberapa kalimat
positif. Kalimat negatif memastikan keluhan ringan zona hijau tidak menghentikan sesi.
"""

import pytest

from app.ai.eir.tanda_bahaya import POLA_TANDA_BAHAYA, RedFlagDetector, normalisasi

SKENARIO_BAHAYA = {
    "nyeri_dada": [
        "dada saya seperti ditekan",  # TC-14
        "Dada rasanya tertindih benda berat",
        "nyeri dada menjalar ke lengan kiri",
        "sakit di dada sampai tembus ke punggung",
        "dada berat dan keluar keringat dingin",
    ],
    "sesak_berat": [
        "saya gak bisa napas",
        "susah bernafas dari tadi",
        "sesak banget sampai susah bicara",
        "napasnya tersengal-sengal",
        "rasanya tercekik",
    ],
    "gejala_stroke": [
        "bicaranya pelo sejak tadi pagi",
        "wajahnya mencong ke kanan",
        "tangan sebelah kiri lemah",
        "kaki kanan mendadak lemah",
        "separuh badan mati rasa",
    ],
    "kejang": ["anak saya kejang di rumah", "tadi kelojotan", "dia step waktu demam"],
    "penurunan_kesadaran": [
        "ibu saya tadi pingsan",
        "sempat tidak sadarkan diri",
        "bapak susah dibangunkan",
        "tiba-tiba bingung dan linglung",
    ],
    "perdarahan_cerna": ["muntah darah dua kali", "BAB hitam seperti aspal", "batuk berdarah", "berak ada darahnya"],
    "perdarahan_banyak": ["darahnya ngucur terus", "luka berdarah tidak mau berhenti", "perdarahan banyak sekali"],
    "perdarahan_kehamilan": [
        "saya hamil 7 bulan keluar flek",
        "keluar darah padahal sedang hamil",
        "ketuban pecah, saya hamil tua",
        "keluar darah dari jalan lahir",
    ],
    "nyeri_kepala_hebat": [
        "sakit kepala hebat mendadak",
        "kepala sakit luar biasa",
        "kepala rasanya mau pecah",
        "nyeri kepala seperti disambar petir",
    ],
    "kaku_kuduk": ["demam dan leher kaku", "kaku kuduk", "ada bintik merah yang tidak hilang saat ditekan"],
    "reaksi_alergi_berat": [
        "bibir saya bengkak habis makan udang",
        "lidahnya membengkak",
        "gatal-gatal lalu sesak napas",
    ],
    "nyeri_perut_hebat": [
        "perut sakit tidak tertahan",
        "nyeri perut hebat sekali",
        "sakit perut sampai tidak bisa berdiri",
    ],
    "kebiruan": ["bibirnya membiru", "ujung jari kebiruan"],
    "cedera_kepala": [
        "jatuh dari motor kepala terbentur lalu muntah",
        "kepalanya kepentok tembok lalu muntah-muntah",
    ],
    "melukai_diri": ["saya pengen mati aja", "dia mencoba bunuh diri", "dia menelan obat banyak sekali", "overdosis"],
}

KELUHAN_RINGAN = [
    "saya pusing sejak pagi",
    "perut mual dan muntah 2 kali",
    "demam tiga hari",
    "batuk pilek",
    "ada luka gores di kaki",
    "gatal di tangan",
    "nyeri punggung bawah setelah angkat galon",
    "sakit tenggorokan",
    "napas biasa saja",
    "sakit kepala biasa seperti kalau kurang tidur",
    "perut kembung",
    "sudah minum obat maag tadi pagi",
]


@pytest.fixture(scope="module")
def detektor() -> RedFlagDetector:
    return RedFlagDetector()


def test_setiap_kelompok_punya_skenario():
    assert set(SKENARIO_BAHAYA) == {kode for kode, _label, _pola in POLA_TANDA_BAHAYA}


@pytest.mark.parametrize(
    ("kode", "kalimat"), [(kode, kalimat) for kode, daftar in SKENARIO_BAHAYA.items() for kalimat in daftar]
)
def test_tanda_bahaya_tertangkap(detektor, kode, kalimat):
    tanda = detektor.periksa(kalimat)
    assert tanda is not None, kalimat
    assert tanda.kode == kode


@pytest.mark.parametrize("kalimat", KELUHAN_RINGAN)
def test_keluhan_ringan_tidak_memicu(detektor, kalimat):
    assert detektor.periksa(kalimat) is None


def test_penyangkalan_tetap_memicu(detektor):
    # Keputusan E2: penyangkalan tidak dikenali supaya tanda bahaya tidak terlewat.
    assert detektor.periksa("tidak ada nyeri dada seperti ditekan").kode == "nyeri_dada"


def test_normalisasi_ejaan_dan_akhiran():
    assert normalisasi("Sy GAK bisa bernafas!!") == "saya tidak bisa bernapas"
    assert normalisasi("darahnya, wajahnya; tanya") == "darah wajah tanya"
