"""Komponen Eir tanpa basis data: panduan, pencarian TF-IDF, prompt, klien LLM, token, dan agen (FR-08)."""

import json
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from ai_training import evaluasi_eir
from app.ai.eir.agen import PENUTUP, PERTANYAAN_PEMBUKA, PERTANYAAN_UMUM, EirAgent
from app.ai.eir.llm import GroqClient, LlmTidakTersediaError, LlmTiruan
from app.ai.eir.panduan import GuidelineRetriever, PanduanTidakSesuaiError, baca_panduan, muat_panduan
from app.ai.eir.prompt import (
    SKEMA_RINGKASAN,
    PembersihIdentitas,
    PemeriksaKeluaran,
    PenyusunPrompt,
)
from app.ai.eir.tanda_bahaya import ARAHAN_TANDA_BAHAYA, RedFlagDetector
from app.ai.eir.tautan import TautanEir, TokenEirKedaluwarsaError, TokenEirTidakValidError, TokenSesiEir
from app.ai.registry import ModelRegistry
from app.config import Config
from app.models import SesiEir
from app.models.enums import KategoriKeluhan, PengisiEir, StatusSesiEir

FOLDER_PANDUAN = Config.PANDUAN_EIR_PATH
WAKTU = datetime(2026, 10, 17, 3, 0, tzinfo=UTC)


@pytest.fixture(scope="module")
def panduan():
    from pathlib import Path

    return muat_panduan(Path(FOLDER_PANDUAN))


@pytest.fixture(scope="module")
def retriever(panduan):
    return GuidelineRetriever(panduan)


# ---------------------------------------------------------------- panduan dan pencarian


def test_delapan_belas_panduan_satu_per_kategori(panduan):
    assert len(panduan) == 18
    assert {p.kategori for p in panduan} == set(KategoriKeluhan)
    assert all(len(p.pertanyaan) >= 5 and "DRAF" in p.isi for p in panduan)


def _tulis(folder, nama, isi):
    path = folder / nama
    path.write_text(isi, encoding="utf-8")
    return path


@pytest.mark.parametrize(
    ("isi", "pesan"),
    [
        ("# X\nKata kunci: a\n## Pertanyaan inti\n- Tanya?\n", "Kategori"),
        ("Kategori: Batuk saja\nKata kunci: a\n## Pertanyaan inti\n- Tanya?\n", "tidak dikenal"),
        ("Kategori: Demam\n## Pertanyaan inti\n- Tanya?\n", "Kata kunci"),
        ("Kategori: Demam\nKata kunci: a\n## Catatan\nisi\n", "pertanyaan inti"),
    ],
)
def test_panduan_rusak_ditolak(tmp_path, isi, pesan):
    with pytest.raises(PanduanTidakSesuaiError, match=pesan):
        baca_panduan(_tulis(tmp_path, "rusak.md", isi))


def test_folder_panduan_tidak_lengkap_ditolak(tmp_path):
    _tulis(tmp_path, "01.md", "Kategori: Demam\nKata kunci: panas\n## Pertanyaan inti\n- Sejak kapan?\n")
    with pytest.raises(PanduanTidakSesuaiError, match="18 berkas"):
        muat_panduan(tmp_path)


@pytest.mark.parametrize(
    ("teks", "kategori"),
    [
        ("perut saya melilit sejak semalam", KategoriKeluhan.NYERI_PERUT),
        ("badan panas menggigil", KategoriKeluhan.DEMAM),
        ("mencret terus dari pagi", KategoriKeluhan.MUAL_MUNTAH_ATAU_DIARE),
        ("jantung deg-degan", KategoriKeluhan.JANTUNG_BERDEBAR),
        ("kaki saya keseleo waktu main bola", KategoriKeluhan.CEDERA_ATAU_LUKA),
    ],
)
def test_retriever_menemukan_panduan_yang_sesuai(retriever, teks, kategori):
    hasil = retriever.cari(teks)
    assert len(hasil) == 3
    assert hasil[0].kategori == kategori


def test_retriever_tanpa_huruf_tetap_mengembalikan_tiga(retriever):
    assert len(retriever.cari("???")) == 3


# ---------------------------------------------------------------- evaluasi dengan keluhan KTAS


def test_evaluasi_eir_tanpa_data_memenuhi_target(retriever):
    hasil = evaluasi_eir.evaluasi(retriever, RedFlagDetector(), evaluasi_eir.hitung_keluhan(None))
    assert hasil.recall >= evaluasi_eir.TARGET_RECALL
    assert hasil.bahaya_tertangkap == hasil.bahaya_total > 0
    assert hasil.lulus


def test_kategori_ktas_memakai_aturan_data_latih():
    assert evaluasi_eir.kategori_ktas("ant. chest pain") == KategoriKeluhan.NYERI_DADA
    assert evaluasi_eir.kategori_ktas("???") == KategoriKeluhan.LAINNYA


def test_hitung_keluhan_dari_csv(tmp_path):
    data = tmp_path / "data.csv"
    data.write_text("Sex;Chief_complain\n1;Abd  pain\n2;abd pain\n1;fever\n", encoding="cp1254")
    assert evaluasi_eir.hitung_keluhan(data) == {"abd pain": 2, "fever": 1}


def test_evaluasi_mencatat_yang_meleset(retriever, monkeypatch):
    monkeypatch.setattr(evaluasi_eir, "TERJEMAHAN", {"fever": ("jari tersayat pisau", True), "cough": ("batuk", False)})
    hasil = evaluasi_eir.evaluasi(retriever, RedFlagDetector(), evaluasi_eir.Counter({"fever": 3}))
    assert (hasil.bobot_total, hasil.recall, hasil.lulus) == (3, 0.0, False)
    assert hasil.meleset
    assert hasil.bahaya_lolos
    assert evaluasi_eir.HasilEvaluasiEir().recall == 0.0


@pytest.mark.parametrize(("lulus", "kode", "teks"), [(True, 0, "LULUS"), (False, 1, "BELUM LULUS")])
def test_main_evaluasi_eir(capsys, monkeypatch, lulus, kode, teks):
    if not lulus:
        monkeypatch.setattr(evaluasi_eir, "TERJEMAHAN", {"fever": ("jari tersayat pisau", True)})
    assert evaluasi_eir.main([]) == kode
    assert f"Hasil: {teks}" in capsys.readouterr().out


# ---------------------------------------------------------------- pembersih identitas dan prompt


def test_pembersih_menghapus_nama_nik_dan_telepon():
    pembersih = PembersihIdentitas("Siti Aminah Al", "3201234567890123", "081234567890")
    teks = "Nama saya siti AMINAH, NIK 3201234567890123, hp 0812-3456-7890, Al bilang nomor lain 3171000000000001"
    hasil = pembersih.bersihkan(teks)
    assert "siti" not in hasil.lower()
    assert "aminah" not in hasil.lower()
    assert "3201234567890123" not in hasil
    assert "3171000000000001" not in hasil
    assert "0812" not in hasil
    # Bagian nama di bawah tiga huruf tidak dicari supaya kata biasa tidak ikut terhapus.
    assert "Al bilang" in hasil


def test_pembersih_tanpa_nama():
    assert PembersihIdentitas(None).bersihkan("pusing") == "pusing"


def test_penyusun_prompt_tanpa_identitas(panduan):
    penyusun = PenyusunPrompt(PembersihIdentitas("Budi Santoso"), "keluarga")
    riwayat = [
        {"peran": "eir", "teks": PERTANYAAN_PEMBUKA},
        {"peran": "pengisi", "teks": "Budi pusing sejak pagi"},
    ]
    pesan = penyusun.susun(panduan[:3], riwayat)
    assert pesan[0]["role"] == "system"
    assert "keluarga pendamping pasien" in pesan[0]["content"]
    assert panduan[0].isi in pesan[0]["content"]
    assert [p["role"] for p in pesan[1:]] == ["assistant", "user"]
    assert pesan[2]["content"] == "[nama] pusing sejak pagi"
    ringkasan = penyusun.susun_ringkasan(riwayat)
    assert "keluhan_utama" in ringkasan[0]["content"]
    assert "Budi" not in json.dumps(ringkasan)


@pytest.mark.parametrize(
    "teks",
    [
        "Sejak kapan nyeri perutnya terasa?",
        "Apakah masih bisa minum tanpa langsung muntah?",
        "Apakah sudah minum obat untuk keluhan ini?",
    ],
)
def test_pemeriksa_keluaran_menerima_pertanyaan_wajar(teks):
    assert PemeriksaKeluaran().aman(teks)


@pytest.mark.parametrize(
    "teks",
    [
        "Sepertinya Anda terkena maag. Sejak kapan?",
        "Diagnosis awalnya gastritis.",
        "Sebaiknya minum paracetamol dulu ya.",
        "Coba konsumsi antasida 3 kali sehari.",
        "Minum 500 mg setiap 8 jam.",
        "Keluhan ini termasuk zona hijau.",
        "Risk level Anda rendah.",
        "",
        "a" * 301,
    ],
)
def test_pemeriksa_keluaran_menolak(teks):
    assert not PemeriksaKeluaran().aman(teks)


# ---------------------------------------------------------------- klien LLM


class _KlienGroqPalsu:
    def __init__(self, isi=None, galat=None, teks_suara="pusing sejak pagi"):
        self.isi = isi
        self.galat = galat
        self.teks_suara = teks_suara
        self.argumen = {}
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._chat))
        self.audio = SimpleNamespace(transcriptions=SimpleNamespace(create=self._suara))

    def _chat(self, **argumen):
        self.argumen = argumen
        if self.galat:
            raise self.galat
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=self.isi))])

    def _suara(self, **argumen):
        self.argumen = argumen
        if self.galat:
            raise self.galat
        return SimpleNamespace(text=self.teks_suara)


def _groq(klien):
    return GroqClient("kunci", "openai/gpt-oss-20b", "whisper-large-v3-turbo", 10, klien=klien)


def test_groq_chat_memakai_json_schema():
    klien = _KlienGroqPalsu(isi='{"pertanyaan": "Sejak kapan?", "cukup": false}')
    hasil = _groq(klien).chat([{"role": "user", "content": "pusing"}], SKEMA_RINGKASAN, "ringkasan_triase")
    assert hasil == {"pertanyaan": "Sejak kapan?", "cukup": False}
    assert klien.argumen["model"] == "openai/gpt-oss-20b"
    format_respons = klien.argumen["response_format"]
    assert format_respons["type"] == "json_schema"
    assert format_respons["json_schema"] == {"name": "ringkasan_triase", "schema": SKEMA_RINGKASAN, "strict": True}


@pytest.mark.parametrize(
    "klien",
    [_KlienGroqPalsu(galat=TimeoutError("habis")), _KlienGroqPalsu(isi="bukan json"), _KlienGroqPalsu(isi="[1, 2]")],
)
def test_groq_chat_gagal_menjadi_llm_tidak_tersedia(klien, caplog):
    with pytest.raises(LlmTidakTersediaError):
        _groq(klien).chat([{"role": "user", "content": "rahasia pasien"}], {}, "x")
    assert "rahasia pasien" not in caplog.text


def test_groq_transkripsi():
    klien = _KlienGroqPalsu(teks_suara="  pusing sejak pagi  ")
    assert _groq(klien).transkripsi(b"data", "rekaman.webm") == "pusing sejak pagi"
    assert klien.argumen["model"] == "whisper-large-v3-turbo"
    assert klien.argumen["language"] == "id"
    with pytest.raises(LlmTidakTersediaError):
        _groq(_KlienGroqPalsu(galat=ConnectionError())).transkripsi(b"data", "rekaman.webm")


def test_groq_client_asli_dibuat_dengan_batas_waktu():
    groq = GroqClient("kunci-tes", "m", "w", 10)
    assert groq.klien.timeout == 10
    assert groq.klien.max_retries == 1


def test_llm_tiruan():
    llm = LlmTiruan()
    pesan = [{"role": "system", "content": "x"}, {"role": "user", "content": "pusing"}]
    assert llm.chat(pesan, {}, "pertanyaan_berikutnya") == {"pertanyaan": LlmTiruan.PERTANYAAN[0], "cukup": False}
    assert llm.chat(pesan, {}, "ringkasan_triase")["keluhan_utama"] == "pusing"
    assert llm.chat(pesan[:1], {}, "ringkasan_triase")["keluhan_utama"] == "Tidak disebutkan"
    assert llm.transkripsi(b"x", "a.webm")
    assert llm.transkripsi(b"", "a.webm") == ""


# ---------------------------------------------------------------- token tautan dan sesi


def test_token_tautan_dan_sesi_tidak_tertukar():
    id_kunjungan = uuid.uuid4()
    tautan = TautanEir("rahasia" * 6, 7200)
    sesi = TokenSesiEir("rahasia" * 6, 7200)
    token = tautan.buat(id_kunjungan)
    assert tautan.baca(token) == id_kunjungan
    with pytest.raises(TokenEirTidakValidError):
        sesi.baca(token, id_kunjungan)


def test_token_sesi_hanya_untuk_sesinya():
    sesi = TokenSesiEir("rahasia" * 6, 7200)
    id_sesi = uuid.uuid4()
    sesi.baca(sesi.buat(id_sesi), id_sesi)
    with pytest.raises(TokenEirTidakValidError, match="tidak berlaku"):
        sesi.baca(sesi.buat(id_sesi), uuid.uuid4())


def test_token_kedaluwarsa_dan_rusak():
    with pytest.raises(TokenEirKedaluwarsaError):
        TautanEir("rahasia" * 6, -1).baca(TautanEir("rahasia" * 6, 7200).buat(uuid.uuid4()))
    with pytest.raises(TokenEirTidakValidError):
        TautanEir("rahasia" * 6, 7200).baca("bukan-token")
    with pytest.raises(TokenEirTidakValidError):
        TautanEir("lain" * 10, 7200).baca(TautanEir("rahasia" * 6, 7200).buat(uuid.uuid4()))


# ---------------------------------------------------------------- EirAgent


class _LlmSkrip(LlmTiruan):
    """LLM palsu yang jawabannya diatur per tes."""

    def __init__(self, pertanyaan="Sejak kapan?", cukup=False, ringkasan=None, galat=False):
        super().__init__()
        self.pertanyaan = pertanyaan
        self.cukup = cukup
        self.ringkasan = ringkasan
        self.galat = galat

    def chat(self, pesan, skema, nama_skema):
        self.panggilan.append({"pesan": pesan, "nama_skema": nama_skema})
        if self.galat:
            raise LlmTidakTersediaError("mati")
        if nama_skema == "ringkasan_triase":
            return self.ringkasan or {
                "keluhan_utama": "Nyeri perut",
                "gejala": "Nyeri perut kanan bawah sejak semalam",
                "onset": "Semalam",
                "kategori_keluhan": "Nyeri perut",
            }
        return {"pertanyaan": self.pertanyaan, "cukup": self.cukup}


def _sesi(jawaban: int = 0) -> SesiEir:
    sesi = SesiEir(pengisi=PengisiEir.PASIEN, status=StatusSesiEir.BERJALAN, transkrip=[])
    sesi.tambah_pesan("eir", PERTANYAAN_PEMBUKA, WAKTU)
    for i in range(jawaban):
        sesi.tambah_pesan("pengisi", "perut sakit" if i == 0 else f"jawaban {i}", WAKTU)
        sesi.tambah_pesan("eir", f"pertanyaan {i}", WAKTU)
    return sesi


def _agen(retriever, llm, **lain):
    return EirAgent(RedFlagDetector(), retriever, llm, lain.get("min_jawaban", 7), lain.get("maks_jawaban", 15))


PEMBERSIH = PembersihIdentitas("Rina")


def test_agen_mulai_dengan_pertanyaan_tetap(retriever):
    sesi = SesiEir(transkrip=[])
    assert _agen(retriever, LlmTiruan()).mulai(sesi, WAKTU) == PERTANYAAN_PEMBUKA
    assert sesi.transkrip[0]["waktu"] == WAKTU.isoformat()


def test_agen_menghentikan_sesi_tanpa_memanggil_llm(retriever):
    llm = _LlmSkrip()
    sesi = _sesi()
    balasan = _agen(retriever, llm).proses(sesi, "dada saya seperti ditekan", PEMBERSIH, WAKTU)
    assert (balasan.status, balasan.pesan, balasan.tanda_bahaya.kode) == (
        StatusSesiEir.DIHENTIKAN,
        ARAHAN_TANDA_BAHAYA,
        "nyeri_dada",
    )
    assert sesi.tanda_bahaya == "Nyeri dada seperti ditekan atau menjalar"
    assert sesi.waktu_selesai == WAKTU
    assert llm.panggilan == []


def test_agen_menyusun_pertanyaan_dari_llm(retriever):
    llm = _LlmSkrip(pertanyaan="Di bagian perut mana sakitnya?")
    sesi = _sesi()
    balasan = _agen(retriever, llm).proses(sesi, "Rina sakit perut sejak semalam", PEMBERSIH, WAKTU)
    assert (balasan.pesan, balasan.jumlah_jawaban, balasan.boleh_selesai) == (
        "Di bagian perut mana sakitnya?",
        1,
        False,
    )
    sistem = llm.panggilan[0]["pesan"][0]["content"]
    assert "Kategori: Nyeri perut" in sistem
    assert "Rina" not in json.dumps(llm.panggilan)
    assert sesi.transkrip[-1] == {"peran": "eir", "teks": "Di bagian perut mana sakitnya?", "waktu": WAKTU.isoformat()}


def test_agen_mengganti_pertanyaan_terlarang_dengan_panduan(retriever):
    sesi = _sesi()
    balasan = _agen(retriever, _LlmSkrip(pertanyaan="Sebaiknya minum obat maag dulu.")).proses(
        sesi, "perut melilit", PEMBERSIH, WAKTU
    )
    assert balasan.pesan in retriever.cari("perut melilit")[0].pertanyaan


def test_pertanyaan_cadangan_tidak_mengulang_lalu_umum(retriever):
    panduan = retriever.cari("demam")[:1]
    sesi = _sesi()
    for pertanyaan in panduan[0].pertanyaan:
        sesi.tambah_pesan("eir", pertanyaan, WAKTU)
    assert EirAgent._pertanyaan_cadangan(sesi, panduan) == PERTANYAAN_UMUM


def test_agen_tidak_tersedia_tetap_mencatat_jawaban(retriever):
    sesi = _sesi()
    with pytest.raises(LlmTidakTersediaError):
        _agen(None, LlmTiruan()).proses(sesi, "pusing", PEMBERSIH, WAKTU)
    assert sesi.jumlah_jawaban == 1
    with pytest.raises(LlmTidakTersediaError):
        _agen(retriever, None).ringkas(sesi, PEMBERSIH, WAKTU)


def test_agen_meringkas_saat_cukup_dan_sudah_tujuh_jawaban(retriever):
    llm = _LlmSkrip(cukup=True)
    sesi = _sesi(jawaban=6)
    balasan = _agen(retriever, llm).proses(sesi, "tidak ada alergi", PEMBERSIH, WAKTU)
    assert (balasan.status, balasan.pesan, balasan.boleh_selesai) == (StatusSesiEir.SELESAI, PENUTUP, False)
    assert sesi.ringkasan["kategori_keluhan"] == "Nyeri perut"


def test_agen_mengabaikan_cukup_sebelum_tujuh_jawaban(retriever):
    balasan = _agen(retriever, _LlmSkrip(cukup=True)).proses(_sesi(jawaban=2), "jawaban", PEMBERSIH, WAKTU)
    assert balasan.status == StatusSesiEir.BERJALAN


def test_agen_meringkas_otomatis_di_jawaban_kelima_belas(retriever):
    llm = _LlmSkrip()
    balasan = _agen(retriever, llm).proses(_sesi(jawaban=14), "jawaban terakhir", PEMBERSIH, WAKTU)
    assert balasan.status == StatusSesiEir.SELESAI
    assert [p["nama_skema"] for p in llm.panggilan] == ["ringkasan_triase"]


def test_ringkasan_yang_tidak_sesuai_skema_ditolak(retriever):
    llm = _LlmSkrip(ringkasan={"keluhan_utama": "", "gejala": "x", "onset": "x", "kategori_keluhan": "Batuk"})
    sesi = _sesi(jawaban=7)
    with pytest.raises(LlmTidakTersediaError, match="skema"):
        _agen(retriever, llm).ringkas(sesi, PEMBERSIH, WAKTU)
    assert sesi.status == StatusSesiEir.BERJALAN


# ---------------------------------------------------------------- ModelRegistry


def test_registry_memuat_eir_tiruan():
    registry = ModelRegistry()
    registry.muat_eir(FOLDER_PANDUAN, "tiruan")
    assert isinstance(registry.llm, LlmTiruan)
    assert len(registry.retriever.panduan) == 18


def test_registry_memuat_groq_bila_ada_kunci():
    registry = ModelRegistry()
    registry.muat_eir(FOLDER_PANDUAN, "groq", api_key="kunci", model="m", model_suara="w", batas_waktu=10)
    assert isinstance(registry.llm, GroqClient)


def test_registry_tanpa_kunci_dan_panduan(tmp_path, caplog):
    registry = ModelRegistry()
    registry.muat_eir(str(tmp_path), "groq", api_key=None)
    assert registry.llm is None
    assert registry.retriever is None
    assert "GROQ_API_KEY kosong" in caplog.text
    assert "Panduan Eir gagal dimuat" in caplog.text
