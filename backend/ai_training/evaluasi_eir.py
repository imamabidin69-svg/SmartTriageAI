"""Evaluasi Eir dengan keluhan dari dataset KTAS (Kaggle, Moon dkk. 2019).

Dataset KTAS tidak berisi percakapan anamnesis, jadi hanya dipakai untuk dua pemeriksaan:

1. Recall@3 GuidelineRetriever: keluhan yang paling sering muncul diterjemahkan ke kalimat pasien, lalu
   dicek apakah panduan kategori yang benar masuk tiga besar. Kategori yang benar diambil dari aturan
   yang sama dengan saat model Random Forest dilatih (ml-service/triase_data.py, ATURAN_KELUHAN).
2. Cakupan RedFlagDetector: keluhan yang ditandai sebagai tanda bahaya harus tertangkap semua (NFR-04).

Setiap keluhan diberi bobot jumlah kemunculannya di data.csv. Lisensi dataset belum jelas, jadi data.csv
tidak ikut di repo; berikan path-nya saat menjalankan:

    python -m ai_training.evaluasi_eir --data ../ml-service/data.csv
"""

import argparse
import csv
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from app.ai.eir.panduan import GuidelineRetriever, muat_panduan
from app.ai.eir.tanda_bahaya import RedFlagDetector
from app.config import DIREKTORI_BACKEND
from app.models.enums import KategoriKeluhan

FOLDER_PANDUAN = DIREKTORI_BACKEND / "app" / "ai" / "artefak" / "panduan"
# Notebook riset mencatat Recall@3 TF-IDF 0,86 (Desain 7.2); angka ini dipakai sebagai batas lulus.
TARGET_RECALL = 0.86

# Disalin dari ml-service/triase_data.py supaya label kategori sama persis dengan data latih model.
ATURAN_KELUHAN = [
    (
        "Penurunan kesadaran atau kejang",
        r"syncope|seiz|sezure|convuls|\bfit\b|mental|altered ment|consciousness"
        r"|unconscious|stupor|coma|drows|faint|\bloc\b|\bcpr\b|arrest|amnesia|delirium",
    ),
    ("Nyeri dada", r"chest"),
    ("Sesak napas atau batuk", r"dyspnea|dysnea|shortness|breath|\bsob\b|wheez|cough|hyperventil"),
    ("Perdarahan", r"bleed|hematemesis|melena|hematochezia|epistaxis|hematuria|hemorrhage|bloody|hemoptysis"),
    (
        "Gangguan saraf",
        r"dysarthria|hemipar|pares|paralysis|palsy|numb|motor weakness|slurred|aphasia"
        r"|facial droop|gait",
    ),
    (
        "Nyeri perut",
        r"\babd|abdom|epigastr|umbilic|\bruq\b|\bluq\b|\brlq\b|\bllq\b|stomach|distension|colic"
        r"|dyspepsia|indigestion|hernia",
    ),
    ("Demam", r"fever|febrile|chill"),
    ("Pusing", r"dizz|vertigo"),
    ("Nyeri kepala", r"headache|head ache|migraine|\bha\b"),
    ("Mual, muntah, atau diare", r"vomit|nausea|diarrhea|diarrhoea|emesis|constipation"),
    (
        "Cedera atau luka",
        r"injur|wound|lacerat|\blac\b|fractur|contusion|burn|bite|abrasion|trauma|\bfall"
        r"|accident|sprain|stab|\bcut\b|crush|foreign body|amputat|swallow|ingestion",
    ),
    ("Jantung berdebar", r"palpitation"),
    ("Kulit atau alergi", r"rash|urticar|itch|prurit|skin|allerg|angioedema|erythema"),
    (
        "Mata, telinga, hidung, atau tenggorokan",
        r"ocular|otalgia|\beye|vision|throat|\bear\b|\bnose|tonsil"
        r"|hearing|tinnitus|dysphagia|facial",
    ),
    (
        "Nyeri punggung, pinggang, atau anggota gerak",
        r"back|flank|\bleg\b|\barm\b|forearm|ankle|finger|knee"
        r"|shoulder|neck|\bhip\b|foot|hand|\btoe|wrist|elbow|extremit|limb|thigh|calf|swelling|joint|pelvi|groin",
    ),
    ("Lemas atau kelemahan umum", r"weak|fatigue|malaise|general|myalgia|lethargy|tired"),
    ("Keluhan kemih atau kandungan", r"urin|voiding|oliguria|dysuria|vagin|genital|scrot|testic|pregnan|menstr"),
]
_ATURAN = [(KategoriKeluhan(nama), re.compile(pola)) for nama, pola in ATURAN_KELUHAN]

# Keluhan terbanyak di data.csv (mencakup sekitar dua pertiga baris) dan kalimat pasien padanannya.
# True berarti keluhan ini harus memicu tanda bahaya.
TERJEMAHAN: dict[str, tuple[str, bool]] = {
    "abd pain": ("perut saya sakit sejak tadi pagi", False),
    "dyspnea": ("saya sesak napas", False),
    "dizziness": ("kepala pusing dari kemarin", False),
    "fever": ("badan saya demam sudah dua hari", False),
    "ant. chest pain": ("dada bagian depan sakit", False),
    "open wound": ("ada luka terbuka di kaki karena kena seng", False),
    "headache": ("sakit kepala", False),
    "epigastric pain": ("ulu hati perih", False),
    "mental change": ("bapak saya tiba-tiba bingung dan linglung", True),
    "general weakness": ("badan lemas tidak bertenaga", False),
    "pain, chest": ("nyeri di dada", False),
    "vomiting": ("muntah terus dari pagi", False),
    "hematemesis": ("saya muntah darah", True),
    "vaginal bleeding": ("keluar darah dari jalan lahir", True),
    "left chest pain": ("dada kiri sakit", False),
    "abd. pain": ("sakit perut", False),
    "lt flank pain": ("pinggang kiri sakit", False),
    "syncope": ("tadi saya pingsan di rumah", True),
    "dysarthria": ("bicaranya jadi pelo", True),
    "abdomen pain": ("perut nyeri", False),
    "palpitation": ("jantung berdebar-debar", False),
    "facial injury": ("wajah luka karena jatuh dari motor", False),
    "ruq pain": ("perut kanan atas sakit", False),
    "urticarial rash": ("badan bentol-bentol gatal biduran", False),
    "melena": ("BAB warnanya hitam", True),
    "pain, abdominal": ("nyeri perut", False),
    "post seizure": ("anak saya tadi kejang", True),
    "hematochezia": ("BAB ada darahnya", True),
    "h-headache": ("kepala sakit cekot-cekot", False),
    "pain, low back": ("punggung bawah sakit", False),
    "rt. flank pain": ("pinggang kanan nyeri", False),
    "discomfort, chest": ("dada rasanya tidak enak", False),
    "epistaxis": ("mimisan dari tadi", False),
    "distension, abd": ("perut kembung dan begah", False),
    "rt. side motor weakness": ("tangan dan kaki sebelah kanan lemah", True),
    "ocular pain, lt.": ("mata kiri sakit", False),
    "ha": ("kepala nyeri", False),
    "ankle injury": ("pergelangan kaki terkilir", False),
    "ocular pain, rt.": ("mata kanan perih", False),
    "cough": ("batuk terus", False),
    "diarrhea": ("mencret dari semalam", False),
    "acute epigastric pain": ("ulu hati tiba-tiba sakit", False),
    "skin rash": ("kulit merah-merah ruam", False),
    "throat pain": ("tenggorokan sakit buat menelan", False),
    "both leg pain": ("kedua kaki sakit", False),
    "upper abdominal pain": ("perut bagian atas nyeri", False),
    "llq pain": ("perut kiri bawah sakit", False),
    "rlq pain": ("perut kanan bawah nyeri", False),
    "pain, flank": ("nyeri pinggang", False),
    "dysuria": ("kencing terasa perih anyang-anyangan", False),
    "myalgia": ("badan pegal semua", False),
    "leg pain": ("kaki sakit", False),
    "convulsion": ("dia kejang-kejang", True),
    "nausea": ("mual terus", False),
    "dz - dizziness": ("pusing kliyengan", False),
    "lbp - low back pain": ("sakit pinggang bawah", False),
    "left leg pain": ("kaki kiri nyeri", False),
    "acute dyspnea": ("tiba-tiba sesak", False),
    "d - diarrhea": ("diare", False),
    "chest palpitation": ("dada berdebar", False),
    "facial palsy": ("mulutnya mencong ke kiri", True),
    "rt abd pain": ("perut sebelah kanan sakit", False),
    "diffuse abdominal pain": ("seluruh perut sakit", False),
    "finger laceration": ("jari tersayat pisau", False),
    "finger injury": ("jari terjepit pintu", False),
    "injury, finger": ("jari cedera", False),
    "abdominal pain (finding)": ("perut terasa sakit", False),
    "lip laceration": ("bibir robek karena jatuh", False),
    "arm injury": ("lengan cedera habis jatuh", False),
    "diffuse chest discomfort": ("dada tidak nyaman", False),
    "suicidal attempt": ("dia tadi mencoba bunuh diri", True),
    "motor weakness": ("tangan dan kaki lemah sebelah", True),
    "amnesia": ("tidak ingat kejadian tadi, sempat tidak sadar", True),
    "post neck pain": ("leher belakang sakit", False),
    "head trauma": ("kepala terbentur tembok", False),
    "blurred vision": ("penglihatan kabur", False),
    "abdominal pain, rt": ("nyeri perut kanan", False),
    "anxiety": ("saya cemas dan gelisah terus", False),
}


def normalisasi_keluhan(teks: str) -> str:
    return " ".join(teks.lower().split())


def kategori_ktas(keluhan: str) -> KategoriKeluhan:
    for kategori, pola in _ATURAN:
        if pola.search(keluhan.lower()):
            return kategori
    return KategoriKeluhan.LAINNYA


def hitung_keluhan(path: Path | None) -> Counter:
    """Jumlah kemunculan tiap keluhan di data.csv. Tanpa data, setiap keluhan berbobot satu."""
    if path is None:
        return Counter(dict.fromkeys(TERJEMAHAN, 1))
    with path.open(encoding="cp1254", newline="") as berkas:
        baris = csv.DictReader(berkas, delimiter=";")
        return Counter(normalisasi_keluhan(b["Chief_complain"]) for b in baris)


@dataclass
class HasilEvaluasiEir:
    bobot_total: int = 0
    bobot_tepat: int = 0
    bahaya_total: int = 0
    bahaya_tertangkap: int = 0
    meleset: list[str] = field(default_factory=list)
    bahaya_lolos: list[str] = field(default_factory=list)

    @property
    def recall(self) -> float:
        return round(self.bobot_tepat / self.bobot_total, 3) if self.bobot_total else 0.0

    @property
    def lulus(self) -> bool:
        return self.recall >= TARGET_RECALL and not self.bahaya_lolos


def evaluasi(retriever: GuidelineRetriever, detektor: RedFlagDetector, jumlah: Counter) -> HasilEvaluasiEir:
    hasil = HasilEvaluasiEir()
    for keluhan, (kalimat, harus_bahaya) in TERJEMAHAN.items():
        bobot = jumlah.get(keluhan, 0)
        if not bobot:
            continue
        kategori = kategori_ktas(keluhan)
        hasil.bobot_total += bobot
        tiga_besar = [p.kategori for p in retriever.cari(kalimat)]
        if kategori in tiga_besar:
            hasil.bobot_tepat += bobot
        else:
            hasil.meleset.append(f"{kalimat!r} ({keluhan}): harapan {kategori.value}, dapat {tiga_besar[0].value}")
        if harus_bahaya:
            hasil.bahaya_total += 1
            if detektor.periksa(kalimat):
                hasil.bahaya_tertangkap += 1
            else:
                hasil.bahaya_lolos.append(f"{kalimat!r} ({keluhan})")
    return hasil


def argumen(args: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluasi pencarian panduan dan tanda bahaya Eir.")
    parser.add_argument("--data", type=Path, help="data.csv KTAS. Tanpa ini setiap keluhan berbobot satu.")
    parser.add_argument("--panduan", type=Path, default=FOLDER_PANDUAN, help="Folder 18 berkas panduan.")
    return parser.parse_args(args)


def main(args: list[str] | None = None) -> int:
    a = argumen(args)
    retriever = GuidelineRetriever(muat_panduan(a.panduan))
    hasil = evaluasi(retriever, RedFlagDetector(), hitung_keluhan(a.data))
    print(f"Recall@3 panduan: {hasil.recall} (target {TARGET_RECALL}, bobot {hasil.bobot_total} baris)")
    print(f"Tanda bahaya tertangkap: {hasil.bahaya_tertangkap} dari {hasil.bahaya_total}")
    for baris in hasil.meleset:
        print(f"  meleset: {baris}")
    for baris in hasil.bahaya_lolos:
        print(f"  tanda bahaya lolos: {baris}")
    print(f"Hasil: {'LULUS' if hasil.lulus else 'BELUM LULUS'}")
    return 0 if hasil.lulus else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
