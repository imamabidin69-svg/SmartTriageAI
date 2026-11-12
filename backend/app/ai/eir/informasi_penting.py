"""DetektorInformasiPenting: menandai keterangan keluarga yang perlu segera diketahui tim ICU, tanpa LLM (FR-08).

Keluarga pasien ICU tidak sedang dalam kondisi gawat, jadi Eir tidak menghentikan percakapan. Yang dicari adalah
informasi yang memengaruhi tindakan di ICU, misalnya alergi obat atau pemakaian obat pengencer darah. Labelnya
disimpan di sesi dan muncul sebagai peringatan untuk perawat.

Daftar pola ini DRAF dan wajib diperiksa tenaga medis sebelum dipakai di ICU sungguhan.
"""

import re
from dataclasses import dataclass

# Singkatan dan ejaan sehari-hari yang sering muncul di chat, diseragamkan sebelum pola dicocokkan.
EJAAN_BAKU = {
    "gak": "tidak",
    "ga": "tidak",
    "gk": "tidak",
    "nggak": "tidak",
    "ngga": "tidak",
    "enggak": "tidak",
    "tdk": "tidak",
    "tak": "tidak",
    "sy": "saya",
    "sdh": "sudah",
    "udah": "sudah",
    "blm": "belum",
    "dgn": "dengan",
    "yg": "yang",
    "obatnya": "obat",
    "nafas": "napas",
    "alergian": "alergi",
    "elergi": "alergi",
    "parasetamol": "paracetamol",
    "amoksisilin": "amoxicillin",
    "amoxilin": "amoxicillin",
}

# Kata penyangkal yang membatalkan temuan bila muncul tepat sebelum pola, misalnya "tidak ada alergi obat".
POLA_PENYANGKAL = re.compile(r"\b(tidak|belum|bukan|tanpa|tidak pernah|tidak ada)\b(?!.*\b(tapi|tetapi|namun)\b)")
JARAK_PENYANGKAL = 25

# (kode, label untuk perawat, pola, periksa_penyangkal).
POLA_INFORMASI_PENTING: tuple[tuple[str, str, str, bool], ...] = (
    (
        "alergi_obat",
        "Alergi obat",
        r"alergi\b.{0,40}\b(obat|antibiotik|amoxicillin|penisilin|penicillin|ampisilin|sulfa|aspirin|ibuprofen"
        r"|asam mefenamat|antalgin|metamizol|paracetamol|cefadroxil|ceftriaxone|kontras|bius|anestesi|yodium)"
        r"|(obat|antibiotik|suntikan|disuntik)\b.{0,40}\b(langsung )?(gatal|biduran|bentol|bengkak|sesak)",
        True,
    ),
    (
        "alergi_lain",
        "Alergi makanan atau bahan lain",
        r"alergi\b.{0,30}\b(makanan|udang|seafood|makanan laut|telur|kacang|susu|ikan|kepiting|cumi|plester"
        r"|lateks|karet|debu)",
        True,
    ),
    (
        "pengencer_darah",
        "Memakai obat pengencer darah",
        r"pengencer darah|warfarin|simarc|clopidogrel|plavix|aspilet|heparin|rivaroxaban|xarelto|apixaban"
        r"|eliquis|dabigatran|cilostazol|ticagrelor|brilinta",
        True,
    ),
    (
        "insulin",
        "Memakai insulin",
        r"\binsulin\b|suntik (gula|diabetes)|lantus|novorapid|levemir|humalog|apidra|sansulin",
        True,
    ),
    (
        "kehamilan",
        "Sedang hamil atau baru melahirkan",
        r"\bhamil\b|\bmengandung\b|baru (saja )?melahirkan|habis melahirkan|pasca melahirkan|keguguran|nifas",
        True,
    ),
    (
        "alat_implan",
        "Memakai alat pacu jantung atau implan",
        r"pacu jantung|pacemaker|ring jantung|pasang ring|\bstent\b|katup jantung|pasang pen|\bpen\b di|implan",
        True,
    ),
    (
        "masalah_pembiusan",
        "Pernah bermasalah saat dibius",
        r"(bius|dibius|anestesi|pembiusan)\b.{0,40}\b(lama( sekali| banget)? (baru )?sadar|susah sadar|reaksi|masalah"
        r"|sesak|demam tinggi|kejang|alergi)"
        r"|(reaksi|masalah|alergi)\b.{0,30}\b(bius|dibius|anestesi|pembiusan)",
        True,
    ),
    (
        "penyakit_menular",
        "Riwayat penyakit menular",
        r"\btbc\b|\btb paru\b|tuberkulosis|flek paru|\bhiv\b|\baids\b|hepatitis b|hepatitis c|\bhepatitis\b",
        True,
    ),
    (
        "keinginan_pasien",
        "Keinginan pasien tentang perawatan",
        r"(tidak|jangan) (mau|ingin|boleh)\b.{0,30}\b(dipasang|alat bantu napas|ventilator|diresusitasi|resusitasi"
        r"|cuci darah|dioperasi|dipacu)|jangan\b.{0,10}\b(dipasang|diresusitasi|resusitasi|dioperasi|cuci darah)"
        r"|\bdnr\b|wasiat",
        False,
    ),
)


@dataclass(frozen=True)
class InformasiPenting:
    kode: str
    label: str


def _kata_dasar(kata: str) -> str:
    # Akhiran -nya dibuang supaya "alerginya" atau "obatnya" cocok dengan pola "alergi" dan "obat".
    if len(kata) > 5 and kata.endswith("nya"):
        kata = kata[:-3]
    return EJAAN_BAKU.get(kata, kata)


def normalisasi(teks: str) -> str:
    """Huruf kecil, tanda baca menjadi spasi (kecuali tanda hubung), dan ejaan sehari-hari diseragamkan."""
    return " ".join(_kata_dasar(k) for k in re.sub(r"[^\w\s-]", " ", teks.lower()).split())


def _klausa(teks: str) -> list[str]:
    """Kalimat dipotong di tanda baca dan kata sambung, supaya penyangkal di klausa lain tidak terbawa."""
    return [normalisasi(k) for k in re.split(r"[.,;!?\n]|\b(?:tapi|tetapi|namun|kecuali)\b", teks, flags=re.I) if k]


class DetektorInformasiPenting:
    def __init__(self, pola: tuple[tuple[str, str, str, bool], ...] = POLA_INFORMASI_PENTING) -> None:
        self.pola = [(InformasiPenting(kode, label), re.compile(regex), cek) for kode, label, regex, cek in pola]

    def periksa(self, teks: str) -> list[InformasiPenting]:
        """Semua informasi penting di satu pesan, sesuai urutan pola dan tanpa duplikat."""
        hasil: list[InformasiPenting] = []
        for klausa in _klausa(teks):
            for info, regex, cek_penyangkal in self.pola:
                cocok = regex.search(klausa)
                if cocok is None or info in hasil:
                    continue
                awal = klausa[max(0, cocok.start() - JARAK_PENYANGKAL) : cocok.start()]
                if cek_penyangkal and POLA_PENYANGKAL.search(awal):
                    continue
                hasil.append(info)
        return sorted(hasil, key=lambda info: [p[0].kode for p in self.pola].index(info.kode))
