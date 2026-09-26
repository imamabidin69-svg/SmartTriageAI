"""Persiapan data KTAS dan pembanding untuk SmartTriage AI.

Dipakai oleh notebook di folder ini supaya pembersihan data, pemetaan label,
dan baseline aturan tidak ditulis ulang di tiap notebook.
"""
import re

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import cohen_kappa_score, f1_score
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

SEED = 42

# urutan dari paling ringan ke paling gawat, dipakai untuk kode 0..3
URUTAN = ["rendah", "sedang", "tinggi", "kritis"]
KODE = {nama: i for i, nama in enumerate(URUTAN)}
PETA_LEVEL = {1: "kritis", 2: "tinggi", 3: "sedang", 4: "rendah", 5: "rendah"}

# penanda nilai hilang di data.csv ("#BOŞ!" = kosong versi Excel Turki)
KODE_HILANG = ["??", "#BOŞ!", ""]
SPO2_MASUK_AKAL = 50  # di bawah ini dianggap salah input (ada satu nilai 20)

# fitur yang nanti tersedia di aplikasi: 6 tanda vital + usia, jenis kelamin
# (dari data pendaftaran) + skala nyeri, kesadaran, kategori keluhan (isian baru)
FITUR = ["Sex", "Age", "kategori_keluhan", "Mental", "NRS_pain",
         "SBP", "DBP", "HR", "RR", "BT", "Saturation"]

# ditambah dua fitur turunan domain dari Soal 3 (lihat tambah_fitur_turunan)
FITUR_LENGKAP = FITUR + ["map", "shock_index"]

KOLOM_DIBUANG = {
    "KTAS_expert": "label yang harus ditebak",
    "KTAS_RN": "penilaian perawat, hanya dipakai sebagai pembanding",
    "Diagnosis in ED": "baru diketahui setelah pemeriksaan",
    "Disposition": "hasil akhir kunjungan",
    "Length of stay_min": "lama tinggal, baru diketahui belakangan",
    "KTAS duration_min": "lama proses triase, bukan kondisi pasien",
    "Error_group": "turunan dari selisih perawat dan pakar",
    "mistriage": "turunan dari selisih perawat dan pakar",
    "Group": "asal IGD, untuk audit saja",
    "Patients number per hour": "beban IGD, bukan kondisi pasien",
    "Arrival mode": "tidak dikumpulkan aplikasi",
    "Injury": "tidak dikumpulkan aplikasi, sebagian tertangkap kategori keluhan",
    "Pain": "sudah tercakup NRS_pain (0 = tidak nyeri)",
    "Chief_complain": "diganti kategori_keluhan",
}

# Kategori keluhan. Urutan penting: aturan pertama yang cocok yang dipakai,
# jadi yang paling gawat ditaruh di atas.
ATURAN_KELUHAN = [
    ("Penurunan kesadaran atau kejang", r"syncope|seiz|sezure|convuls|\bfit\b|mental|altered ment|consciousness|unconscious|stupor|coma|drows|faint|\bloc\b|\bcpr\b|arrest|amnesia|delirium"),
    ("Nyeri dada", r"chest"),
    ("Sesak napas atau batuk", r"dyspnea|dysnea|shortness|breath|\bsob\b|wheez|cough|hyperventil"),
    ("Perdarahan", r"bleed|hematemesis|melena|hematochezia|epistaxis|hematuria|hemorrhage|bloody|hemoptysis"),
    ("Gangguan saraf", r"dysarthria|hemipar|pares|paralysis|palsy|numb|motor weakness|slurred|aphasia|facial droop|gait"),
    ("Nyeri perut", r"\babd|abdom|epigastr|umbilic|\bruq\b|\bluq\b|\brlq\b|\bllq\b|stomach|distension|colic|dyspepsia|indigestion|hernia"),
    ("Demam", r"fever|febrile|chill"),
    ("Pusing", r"dizz|vertigo"),
    ("Nyeri kepala", r"headache|head ache|migraine|\bha\b"),
    ("Mual, muntah, atau diare", r"vomit|nausea|diarrhea|diarrhoea|emesis|constipation"),
    ("Cedera atau luka", r"injur|wound|lacerat|\blac\b|fractur|contusion|burn|bite|abrasion|trauma|\bfall|accident|sprain|stab|\bcut\b|crush|foreign body|amputat|swallow|ingestion"),
    ("Jantung berdebar", r"palpitation"),
    ("Kulit atau alergi", r"rash|urticar|itch|prurit|skin|allerg|angioedema|erythema"),
    ("Mata, telinga, hidung, atau tenggorokan", r"ocular|otalgia|\beye|vision|throat|\bear\b|\bnose|tonsil|hearing|tinnitus|dysphagia|facial"),
    ("Nyeri punggung, pinggang, atau anggota gerak", r"back|flank|\bleg\b|\barm\b|forearm|ankle|finger|knee|shoulder|neck|\bhip\b|foot|hand|\btoe|wrist|elbow|extremit|limb|thigh|calf|swelling|joint|pelvi|groin"),
    ("Lemas atau kelemahan umum", r"weak|fatigue|malaise|general|myalgia|lethargy|tired"),
    ("Keluhan kemih atau kandungan", r"urin|voiding|oliguria|dysuria|vagin|genital|scrot|testic|pregnan|menstr"),
]
_ATURAN_KELUHAN = [(nama, re.compile(pola)) for nama, pola in ATURAN_KELUHAN]


def kategori_keluhan(teks):
    t = str(teks).lower()
    for nama, pola in _ATURAN_KELUHAN:
        if pola.search(t):
            return nama
    return "Lainnya"


def muat_mentah(path="data.csv"):
    """Baca data.csv apa adanya (semua kolom teks), hanya merapikan spasi."""
    df = pd.read_csv(path, sep=";", encoding="cp1254", dtype=str)
    df.columns = [c.strip() for c in df.columns]
    for c in df.columns:
        if c not in ("Chief_complain", "Diagnosis in ED"):
            df[c] = df[c].str.strip()
    return df


def _angka(kolom):
    kolom = kolom.replace(KODE_HILANG, np.nan)
    return pd.to_numeric(kolom.str.replace(",", ".", regex=False), errors="coerce")


def bersihkan(mentah, usia_min=None):
    """Ubah ke angka, tangani nilai hilang, pasang label 4 level dan kategori keluhan."""
    d = mentah.copy()
    for c in ["Group", "Sex", "Age", "Patients number per hour", "Arrival mode", "Injury",
              "Mental", "Pain", "NRS_pain", "SBP", "DBP", "HR", "RR", "BT", "Saturation",
              "KTAS_RN", "KTAS_expert", "Disposition", "Error_group"]:
        d[c] = _angka(d[c])

    # NRS_pain kosong hampir hanya saat tidak nyeri, jadi nilainya 0
    d.loc[(d["Pain"] == 0) & d["NRS_pain"].isna(), "NRS_pain"] = 0
    d.loc[d["Saturation"] < SPO2_MASUK_AKAL, "Saturation"] = np.nan

    d["ktas_pakar"] = d["KTAS_expert"].astype(int)
    d["ktas_perawat"] = d["KTAS_RN"].astype(int)
    d["level_pakar"] = d["ktas_pakar"].map(PETA_LEVEL)
    d["level_perawat"] = d["ktas_perawat"].map(PETA_LEVEL)
    d["y"] = d["level_pakar"].map(KODE)

    d["kategori_keluhan"] = d["Chief_complain"].map(kategori_keluhan)
    d["keluhan_tak_terbaca"] = d["Chief_complain"].str.fullmatch(r"[\?\s]+").fillna(False)

    if usia_min is not None:
        d = d[d["Age"] >= usia_min].reset_index(drop=True)
    return d


def tambah_fitur_turunan(d):
    """Soal 3: MAP dan Shock Index (rumus sama seperti A.6), plus kelompok usia.

    Dipanggil setelah bersihkan(). Baris dengan SBP/DBP/HR kosong akan
    menghasilkan map/shock_index kosong juga (ikut kosong, tidak diisi manual
    di sini; imputer di buat_praproses() yang menanganinya).
    """
    d = d.copy()
    d["map"] = (d["SBP"] + 2 * d["DBP"]) / 3
    d["shock_index"] = d["HR"] / d["SBP"]
    d["kelompok_usia"] = pd.cut(
        d["Age"], bins=[15, 24, 44, 64, 96],
        labels=["remaja_akhir", "dewasa", "paruh_baya", "lansia"])
    return d


def lipatan(y, n_lipatan=5, n_ulang=3):
    """Pembagi validasi silang berstrata berulang. Pakai yang sama untuk semua metode."""
    return RepeatedStratifiedKFold(n_splits=n_lipatan, n_repeats=n_ulang, random_state=SEED)


# ---------- baseline: port dari lib/classify.ts ----------

# Terjemahan kata kunci pada classify.ts (nyeri dada|sesak|tidak sadar|kejang|
# pendarahan hebat) ke bahasa Inggris, karena keluhan di dataset berbahasa Inggris.
KATA_KUNCI_ATURAN = re.compile(
    r"chest"
    r"|dyspnea|dysnea|shortness of breath|\bsob\b"
    r"|unconscious|loss of consciousness|syncope|mental change|altered ment|stupor|coma|\bcpr\b|arrest"
    r"|seizure|sezure|convulsion|\bfit\b"
    r"|massive bleeding|severe bleeding|profuse bleeding|hemorrhage",
    re.I,
)
AMBANG_BAWAAN = {"kritis": 6, "tinggi": 4, "sedang": 2}  # ai-config-store.ts v1.2.0-rule-based


def skor_aturan(r, pakai_kata_kunci=True):
    """Sama dengan classify(): poin per tanda vital, nilai hilang tidak menambah poin."""
    skor = 0
    spo2, sbp, hr, bt, rr = r["Saturation"], r["SBP"], r["HR"], r["BT"], r["RR"]
    if pd.notna(spo2):
        if spo2 < 92:
            skor += 3
        elif spo2 < 95:
            skor += 1
    if pd.notna(sbp):
        if sbp >= 180 or sbp < 90:
            skor += 3
        elif sbp >= 150:
            skor += 1
    if pd.notna(hr) and (hr >= 120 or hr < 50):
        skor += 2
    if pd.notna(bt):
        if bt >= 39:
            skor += 2
        elif bt >= 37.8:
            skor += 1
    if pd.notna(rr) and (rr >= 28 or rr < 10):
        skor += 2
    if pakai_kata_kunci and KATA_KUNCI_ATURAN.search(str(r["Chief_complain"])):
        skor += 3
    return skor


def level_dari_skor(skor, ambang=AMBANG_BAWAAN):
    if skor >= ambang["kritis"]:
        return "kritis"
    if skor >= ambang["tinggi"]:
        return "tinggi"
    if skor >= ambang["sedang"]:
        return "sedang"
    return "rendah"


def prediksi_aturan(d, pakai_kata_kunci=True, ambang=AMBANG_BAWAAN):
    skor = d.apply(lambda r: skor_aturan(r, pakai_kata_kunci), axis=1)
    return skor.map(lambda s: level_dari_skor(s, ambang))


# ---------- metrik ----------

def _ke_kode(level):
    """Terima nama level ("kritis") atau kode 0..3, keluarkan array kode."""
    level = pd.Series(level)
    if level.dtype == object or str(level.dtype).startswith("str"):
        level = level.map(KODE)
    return level.to_numpy()


def metrik(level_benar, level_pred):
    """Metrik yang dijanjikan di dokumen framing, dihitung dari nama level."""
    yb = _ke_kode(level_benar)
    yp = _ke_kode(level_pred)
    gawat = yb >= KODE["tinggi"]
    return {
        "akurasi": float((yb == yp).mean()),
        "macro_f1": float(f1_score(yb, yp, labels=[0, 1, 2, 3], average="macro", zero_division=0)),
        "recall_gawat": float((yp[gawat] >= KODE["tinggi"]).mean()),
        "recall_kritis": float((yp[yb == KODE["kritis"]] == KODE["kritis"]).mean()),
        "under_triage": float((yp < yb).mean()),
        "over_triage": float((yp > yb).mean()),
        "kappa_berbobot": float(cohen_kappa_score(yb, yp, weights="quadratic")),
    }


def matriks_konfusi(level_benar, level_pred):
    return pd.crosstab(
        pd.Categorical(pd.Series(level_benar).to_numpy(), categories=URUTAN),
        pd.Categorical(pd.Series(level_pred).to_numpy(), categories=URUTAN),
        rownames=["pakar"], colnames=["prediksi"], dropna=False,
    )


# ---------- praproses dan evaluasi validasi silang ----------

def buat_praproses(skala=False, fitur=None):
    """One-hot untuk kategori keluhan, median untuk angka yang hilang.

    `fitur`: daftar kolom yang dipakai (default FITUR). Pakai FITUR_LENGKAP
    untuk menyertakan map/shock_index dari tambah_fitur_turunan().
    Status "saturasi terukur atau tidak" sengaja tidak dijadikan fitur (lihat notebook).
    """
    fitur = FITUR if fitur is None else fitur
    angka = [c for c in fitur if c != "kategori_keluhan"]
    langkah = [("isi", SimpleImputer(strategy="median"))]
    if skala:
        langkah.append(("skala", StandardScaler()))
    return ColumnTransformer([
        ("kategori", OneHotEncoder(handle_unknown="ignore"), ["kategori_keluhan"]),
        ("angka", Pipeline(langkah), angka),
    ])


def evaluasi_cv(buat_model, X, level_pakar, pembagi=None):
    """Latih dan uji di tiap lipatan, kembalikan metrik per lipatan (satu baris per lipatan)."""
    y = _ke_kode(level_pakar)
    if pembagi is None:
        pembagi = lipatan(y)
    hasil = []
    for latih, uji in pembagi.split(X, y):
        model = buat_model()
        model.fit(X.iloc[latih], y[latih])
        hasil.append(metrik(y[uji], model.predict(X.iloc[uji])))
    return pd.DataFrame(hasil)
