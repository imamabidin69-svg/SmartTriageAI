"""RedFlagDetector: memeriksa setiap pesan pasien dengan aturan tanda bahaya, tanpa LLM (FR-08, NFR-03).

Daftar pola ini DRAF (keputusan Tahap 4 pilihan A) dan wajib diperiksa tenaga medis sebelum dipakai di IGD
sungguhan. Penyangkalan seperti "tidak ada nyeri dada" sengaja tidak dikenali (keputusan E2): lebih baik perawat
datang memeriksa karena alarm palsu daripada tanda bahaya yang sebenarnya terlewat.
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
    "bgt": "banget",
    "sy": "saya",
    "sdh": "sudah",
    "udah": "sudah",
    "blm": "belum",
    "bs": "bisa",
    "dgn": "dengan",
    "yg": "yang",
    "jd": "jadi",
    "tb2": "tiba-tiba",
    "tiba2": "tiba-tiba",
    "nafas": "napas",
    "bernafas": "bernapas",
    "sesek": "sesak",
    "kpl": "kepala",
    "pendarahan": "perdarahan",
    "bab": "berak",
}

# (kode, label untuk perawat, pola). Label ini yang muncul di peringatan GET /peringatan.
POLA_TANDA_BAHAYA: tuple[tuple[str, str, str], ...] = (
    (
        "nyeri_dada",
        "Nyeri dada seperti ditekan atau menjalar",
        r"dada\b.{0,30}\b(di|ter)(tekan|tindih|remas|himpit|hantam)"
        r"|dada\b.{0,20}\b(berat|panas)\b.{0,40}\b(keringat dingin|berkeringat)"
        r"|(nyeri|sakit|ngilu|panas)\b.{0,20}\bdada\b.{0,40}\b(menjalar|tembus|nembus|sampai)\b"
        r".{0,20}\b(lengan|tangan|rahang|leher|punggung|bahu)",
    ),
    (
        "sesak_berat",
        "Sesak napas berat",
        r"(tidak|susah|sulit|sukar)\b.{0,10}\b(bisa )?(bernapas|napas|ambil napas)"
        r"|sesak\b.{0,30}\b(berat|parah|sekali|banget|makin|tidak bisa bicara|sulit bicara|susah bicara)"
        r"|napas\b.{0,20}\b(tersengal|megap|tercekik|terputus|pendek-pendek)"
        r"|megap-megap|tersengal-sengal|tercekik",
    ),
    (
        "gejala_stroke",
        "Bicara pelo, wajah mencong, atau lemah sesisi",
        r"\bpelo\b|bicara(nya)?\b.{0,15}\b(cadel|tidak jelas|kacau|aneh|berantakan)"
        r"|(wajah|muka|mulut|bibir)\b.{0,15}\b(mencong|miring|perot|turun sebelah|tertarik)"
        r"|(lemah|lumpuh|kebas|mati rasa|tidak bisa digerakkan|tidak bisa diangkat)\b.{0,30}"
        r"\b(sebelah|separuh|satu sisi|sisi kiri|sisi kanan)"
        r"|(sebelah|separuh|satu sisi)\b.{0,30}\b(lemah|lumpuh|kebas|mati rasa|tidak bisa digerakkan)"
        r"|(tangan|kaki|lengan) (kiri|kanan)\b.{0,15}\b(lumpuh|mati rasa|tidak bisa digerakkan|mendadak lemah)",
    ),
    ("kejang", "Kejang", r"\bkejang|kelojotan|\bstep\b|\bsawan\b|\bayan\b"),
    (
        "penurunan_kesadaran",
        "Pingsan atau penurunan kesadaran",
        r"pingsan|tidak sadar|hilang kesadaran|tidak sadarkan diri"
        r"|(tidak bisa|susah|sulit) dibangunkan|tidak (merespons|respon|nyambung)"
        r"|linglung|meracau|ngelantur|(tiba-tiba|mendadak) bingung",
    ),
    (
        "perdarahan_cerna",
        "Muntah darah, batuk darah, atau BAB hitam/berdarah",
        r"(muntah|batuk)\b.{0,15}\b(darah|berdarah|hitam|seperti kopi|ampas kopi)"
        r"|(berak|tinja|feses|buang air besar|kotoran)\b.{0,20}\b(darah|berdarah|hitam)",
    ),
    (
        "perdarahan_banyak",
        "Perdarahan banyak atau tidak berhenti",
        r"(darah|perdarahan|berdarah)\b.{0,30}\b(banyak|deras|mengucur|ngucur|menyembur|nyembur"
        r"|tidak (mau )?berhenti|terus keluar|tidak mampet)",
    ),
    (
        "perdarahan_kehamilan",
        "Keluhan kehamilan dengan perdarahan atau ketuban",
        r"(hamil|kehamilan)\b.{0,60}\b(darah|flek|perdarahan|ketuban|kontraksi|tidak terasa (gerak|bergerak))"
        r"|(darah|flek|perdarahan|ketuban)\b.{0,60}\b(hamil|kehamilan)"
        r"|(darah|perdarahan)\b.{0,20}\b(jalan lahir|vagina|kemaluan)",
    ),
    (
        "nyeri_kepala_hebat",
        "Nyeri kepala hebat mendadak",
        r"kepala\b.{0,30}\b(hebat|terhebat|paling (parah|sakit)|luar biasa"
        r"|seperti (dipukul|disambar|meledak|dihantam))"
        r"|kepala\b.{0,15}\b(mau |seperti )?(pecah|meledak)",
    ),
    (
        "kaku_kuduk",
        "Leher kaku atau bintik merah yang tidak hilang",
        r"kaku kuduk|(leher|tengkuk)\b.{0,10}\bkaku|leher\b.{0,20}\b(tidak bisa|susah|sulit) (ditekuk|menunduk)"
        r"|bintik\b.{0,20}\b(merah|ungu)\b.{0,40}\btidak hilang",
    ),
    (
        "reaksi_alergi_berat",
        "Bengkak bibir, lidah, atau tenggorokan",
        r"(bibir|lidah|tenggorokan|wajah|muka)\b.{0,15}\b(bengkak|membengkak|tebal)"
        r"|tenggorokan\b.{0,20}\b(tercekik|menutup|menyempit)"
        r"|(gatal|biduran|bentol|alergi)\b.{0,50}\b(sesak|susah napas|sulit bernapas|mau pingsan)",
    ),
    (
        "nyeri_perut_hebat",
        "Nyeri perut hebat",
        r"perut\b.{0,30}\b(hebat|luar biasa|tidak tertahan|tidak tahan sakit"
        r"|parah sekali|sampai tidak bisa (berdiri|jalan|bergerak))"
        r"|perut\b.{0,15}\b(keras|kaku) (seperti papan|sekali)",
    ),
    (
        "kebiruan",
        "Bibir atau ujung jari kebiruan",
        r"(bibir|ujung jari|kuku|wajah|muka|lidah)\b.{0,15}\b(membiru|biru|kebiruan|ungu|keunguan)",
    ),
    (
        "cedera_kepala",
        "Benturan kepala dengan muntah, pingsan, atau cairan dari telinga/hidung",
        r"(terbentur|benturan|jatuh|kepentok)\b.{0,40}\bkepala\b.{0,60}\b(muntah|pingsan|tidak sadar"
        r"|keluar (darah|cairan) dari (telinga|hidung))"
        r"|kepala\b.{0,30}\b(terbentur|kepentok)\b.{0,60}\b(muntah|pingsan|tidak sadar)",
    ),
    (
        "melukai_diri",
        "Pikiran bunuh diri atau melukai diri",
        r"bunuh diri|mengakhiri hidup|(ingin|pengen|pingin|mau) mati|tidak (ingin|mau) hidup"
        r"|(menyakiti|melukai) diri|minum racun|overdosis|over dosis|menelan\b.{0,10}\b(obat|racun)\b.{0,15}\bbanyak",
    ),
)

ARAHAN_TANDA_BAHAYA = (
    "Terima kasih sudah menyampaikan. Keluhan ini perlu segera dilihat perawat. "
    "Percakapan kami hentikan dulu. Silakan langsung temui perawat di meja triase sekarang."
)


@dataclass(frozen=True)
class TandaBahaya:
    kode: str
    label: str


def _kata_dasar(kata: str) -> str:
    # Akhiran -nya dibuang supaya "darahnya" atau "wajahnya" cocok dengan pola "darah" dan "wajah".
    if len(kata) > 5 and kata.endswith("nya"):
        kata = kata[:-3]
    return EJAAN_BAKU.get(kata, kata)


def normalisasi(teks: str) -> str:
    """Huruf kecil, tanda baca menjadi spasi (kecuali tanda hubung), dan ejaan sehari-hari diseragamkan."""
    return " ".join(_kata_dasar(k) for k in re.sub(r"[^\w\s-]", " ", teks.lower()).split())


class RedFlagDetector:
    def __init__(self, pola: tuple[tuple[str, str, str], ...] = POLA_TANDA_BAHAYA) -> None:
        self.pola = [(TandaBahaya(kode, label), re.compile(regex)) for kode, label, regex in pola]

    def periksa(self, teks: str) -> TandaBahaya | None:
        bersih = normalisasi(teks)
        for tanda, regex in self.pola:
            if regex.search(bersih):
                return tanda
        return None
