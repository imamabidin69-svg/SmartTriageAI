"""Endpoint Eir (FR-08, Desain 2.8, SKPL TC-14 dan TC-15, keputusan E1-E6)."""

import contextlib
import io
import threading
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from werkzeug.datastructures import FileStorage
from werkzeug.test import encode_multipart

from app.ai.eir.agen import PENUTUP, PERTANYAAN_PEMBUKA
from app.ai.eir.llm import LlmTidakTersediaError, LlmTiruan
from app.ai.eir.tanda_bahaya import ARAHAN_TANDA_BAHAYA
from app.extensions import db
from app.models import Kunjungan, Pasien, SesiEir
from app.models.enums import JenisKelamin, PengisiEir, Peran, RiskLevel, StatusKunjungan, StatusSesiEir
from app.services.eir_service import jenis_audio
from app.utils.errors import Tipe, ValidasiGagalError

AUDIO_WEBM = b"\x1aE\xdf\xa3" + b"\x00" * 64


class LlmUji(LlmTiruan):
    """LLM tiruan yang bisa dibuat gagal atau memberi pertanyaan tertentu."""

    def __init__(self, gagal=False, pertanyaan=None, teks_suara="pusing sejak pagi", gagal_suara=False):
        super().__init__()
        self.gagal = gagal
        self.pertanyaan = pertanyaan
        self.teks_suara = teks_suara
        self.gagal_suara = gagal_suara
        self.audio: list[tuple[bytes, str]] = []

    def chat(self, pesan, skema, nama_skema):
        if self.gagal:
            raise LlmTidakTersediaError("Groq mati")
        hasil = super().chat(pesan, skema, nama_skema)
        if self.pertanyaan and nama_skema == "pertanyaan_berikutnya":
            hasil["pertanyaan"] = self.pertanyaan
        return hasil

    def transkripsi(self, audio, nama_berkas):
        self.audio.append((audio, nama_berkas))
        if self.gagal_suara:
            raise LlmTidakTersediaError("Groq mati")
        return self.teks_suara


@pytest.fixture
def pakai_llm(app, monkeypatch):
    def _pakai(llm):
        monkeypatch.setattr(app.extensions["model_registry"], "llm", llm)
        return llm

    return _pakai


@pytest.fixture
def llm(pakai_llm):
    return pakai_llm(LlmUji())


@pytest.fixture
def perawat(masuk):
    return masuk(Peran.PERAWAT)


@pytest.fixture
def kunjungan_hijau(buat_kunjungan, buat_triase):
    kunjungan = buat_kunjungan(nama="Rina Marlina", nik="3201234567890123", no_telepon="081234567890")
    buat_triase(kunjungan, RiskLevel.RENDAH)
    return kunjungan


def _tautan(client, perawat, kunjungan):
    return client.post(f"/api/v1/kunjungan/{kunjungan.id_kunjungan}/tautan-eir", headers=perawat[1])


def _buka(client, token, pengisi="pasien", setuju=True):
    return client.post("/api/v1/eir/sesi", json={"token": token, "setuju": setuju, "pengisi": pengisi})


@pytest.fixture
def sesi(client, perawat, kunjungan_hijau, llm):
    """Sesi Eir yang sudah dibuka: (id_sesi, header token sesi)."""
    token = _tautan(client, perawat, kunjungan_hijau).get_json()["token"]
    isi = _buka(client, token).get_json()
    return isi["id_sesi"], {"X-Token-Eir": isi["token_sesi"]}


def _pesan(client, sesi, teks="perut saya sakit sejak semalam"):
    id_sesi, header = sesi
    return client.post(f"/api/v1/eir/sesi/{id_sesi}/pesan", json={"teks": teks}, headers=header)


def _selesai(client, sesi):
    id_sesi, header = sesi
    return client.post(f"/api/v1/eir/sesi/{id_sesi}/selesai", headers=header)


def _suara(client, sesi, data: bytes | None = AUDIO_WEBM):
    id_sesi, header = sesi
    isi = {} if data is None else {"berkas": FileStorage(io.BytesIO(data), filename="rekaman.webm")}
    batas, body = encode_multipart(isi)
    return client.post(
        f"/api/v1/eir/sesi/{id_sesi}/suara",
        data=body,
        headers=header,
        content_type=f"multipart/form-data; boundary={batas}",
    )


def _ambil_sesi(id_sesi) -> SesiEir:
    return db.session.scalar(
        select(SesiEir).where(SesiEir.id_sesi == uuid.UUID(id_sesi)).execution_options(populate_existing=True)
    )


# ---------------------------------------------------------------- tautan Eir (perawat)


def test_perawat_membuat_tautan_untuk_zona_hijau(client, perawat, kunjungan_hijau):
    respons = _tautan(client, perawat, kunjungan_hijau)
    assert respons.status_code == 201
    isi = respons.get_json()
    assert isi["url"] == f"http://localhost/eir#t={isi['token']}"
    assert isi["kedaluwarsa"]


@pytest.mark.parametrize("peran", [Peran.DOKTER, Peran.ADMIN])
def test_tautan_hanya_untuk_perawat(client, masuk, kunjungan_hijau, peran):
    assert _tautan(client, masuk(peran), kunjungan_hijau).status_code == 403


def test_tautan_kunjungan_tidak_ada(client, perawat):
    respons = client.post(f"/api/v1/kunjungan/{uuid.uuid4()}/tautan-eir", headers=perawat[1])
    assert respons.status_code == 404


@pytest.mark.parametrize(
    ("level", "status", "pesan"),
    [
        (None, StatusKunjungan.MENUNGGU, "belum ditriase"),
        (RiskLevel.SEDANG, StatusKunjungan.MENUNGGU, "risk level terakhir rendah"),
        (RiskLevel.RENDAH, StatusKunjungan.DITANGANI, "masih menunggu"),
    ],
)
def test_tautan_ditolak_bila_bukan_zona_hijau(client, perawat, buat_kunjungan, buat_triase, level, status, pesan):
    kunjungan = buat_kunjungan(status=status)
    if level is not None:
        buat_triase(kunjungan, level)
    respons = _tautan(client, perawat, kunjungan)
    assert respons.status_code == 409
    assert pesan in respons.get_json()["detail"]


def test_level_terakhir_yang_dipakai(client, perawat, buat_kunjungan, buat_triase):
    # Waktu dibuat eksplisit: dalam satu transaksi tes, now() selalu sama sehingga urutannya tidak pasti.
    kunjungan = buat_kunjungan()
    sekarang = datetime.now(UTC)
    buat_triase(kunjungan, RiskLevel.RENDAH, waktu=sekarang - timedelta(minutes=30))
    buat_triase(kunjungan, RiskLevel.TINGGI, waktu=sekarang)
    assert _tautan(client, perawat, kunjungan).status_code == 409


# ---------------------------------------------------------------- membuka sesi (pasien atau keluarga)


def test_buka_sesi_dengan_persetujuan(client, perawat, kunjungan_hijau, llm):
    token = _tautan(client, perawat, kunjungan_hijau).get_json()["token"]
    respons = _buka(client, token, pengisi="keluarga")
    assert respons.status_code == 201
    isi = respons.get_json()
    assert isi["pesan"] == PERTANYAAN_PEMBUKA
    assert isi["token_sesi"] != token
    sesi = _ambil_sesi(isi["id_sesi"])
    assert (sesi.pengisi.value, sesi.status, sesi.id_kunjungan) == (
        "keluarga",
        StatusSesiEir.BERJALAN,
        kunjungan_hijau.id_kunjungan,
    )
    assert sesi.waktu_persetujuan is not None
    assert sesi.transkrip[0]["peran"] == "eir"


def test_persetujuan_wajib(client, perawat, kunjungan_hijau):
    token = _tautan(client, perawat, kunjungan_hijau).get_json()["token"]
    respons = _buka(client, token, setuju=False)
    assert respons.status_code == 422
    assert respons.get_json()["errors"] == [
        {"field": "setuju", "pesan": "Persetujuan wajib diberikan sebelum memakai Eir."}
    ]


def test_buka_sesi_token_rusak_atau_kedaluwarsa(app, client, perawat, kunjungan_hijau, monkeypatch):
    respons = _buka(client, "bukan-token")
    assert respons.status_code == 401
    assert respons.get_json()["type"] == Tipe.TOKEN_TIDAK_VALID
    token = _tautan(client, perawat, kunjungan_hijau).get_json()["token"]
    monkeypatch.setitem(app.config, "UMUR_TOKEN_EIR_DETIK", -1)
    respons = _buka(client, token)
    assert respons.status_code == 401
    assert respons.get_json()["type"] == Tipe.TOKEN_KEDALUWARSA


def test_buka_sesi_ditolak_bila_pasien_sudah_dipanggil(client, perawat, kunjungan_hijau, sesi_db):
    token = _tautan(client, perawat, kunjungan_hijau).get_json()["token"]
    kunjungan_hijau.status = StatusKunjungan.DITANGANI
    sesi_db.commit()
    assert _buka(client, token).status_code == 409


# ---------------------------------------------------------------- pesan


def test_pesan_mendapat_pertanyaan_berikutnya(client, sesi):
    respons = _pesan(client, sesi)
    assert respons.status_code == 200
    assert respons.get_json() == {
        "status": "berjalan",
        "pesan": LlmTiruan.PERTANYAAN[0],
        "jumlah_jawaban": 1,
        "boleh_selesai": False,
        "transkripsi": None,
    }
    assert [i["peran"] for i in _ambil_sesi(sesi[0]).transkrip] == ["eir", "pengisi", "eir"]


def test_identitas_tidak_dikirim_ke_llm(client, sesi, llm):
    _pesan(client, sesi, "Saya Rina Marlina, NIK 3201234567890123, hp 081234567890, perut sakit")
    terkirim = str(llm.panggilan)
    for rahasia in ("Rina", "Marlina", "3201234567890123", "081234567890"):
        assert rahasia not in terkirim
    # Transkrip di basis data tetap utuh untuk perawat.
    assert "Rina" in _ambil_sesi(sesi[0]).transkrip[1]["teks"]


def test_tanda_bahaya_menghentikan_sesi_dan_memicu_peringatan(client, sesi, llm, masuk):
    # SKPL TC-14: percakapan dihentikan tanpa memanggil LLM dan perawat menerima peringatan.
    respons = _pesan(client, sesi, "dada saya seperti ditekan")
    assert respons.status_code == 200
    assert respons.get_json()["status"] == "dihentikan"
    assert respons.get_json()["pesan"] == ARAHAN_TANDA_BAHAYA
    assert llm.panggilan == []
    peringatan = client.get("/api/v1/peringatan", headers=masuk(Peran.PERAWAT)[1]).get_json()["items"]
    assert [p["jenis"] for p in peringatan] == ["tanda_bahaya_eir"]
    assert "Nyeri dada seperti ditekan" in peringatan[0]["alasan"]
    assert _pesan(client, sesi, "halo").status_code == 409


def test_tanda_bahaya_tetap_berjalan_saat_groq_mati(client, sesi, pakai_llm):
    pakai_llm(LlmUji(gagal=True))
    assert _pesan(client, sesi, "anak saya kejang").get_json()["status"] == "dihentikan"


def test_groq_mati_jawaban_tetap_tersimpan(client, sesi, pakai_llm):
    # Keputusan E3: 503 dengan arahan menemui perawat, sesi tetap berjalan.
    pakai_llm(LlmUji(gagal=True))
    respons = _pesan(client, sesi)
    assert respons.status_code == 503
    assert respons.get_json()["type"] == Tipe.LAYANAN_TIDAK_TERSEDIA
    assert "perawat" in respons.get_json()["detail"]
    tersimpan = _ambil_sesi(sesi[0])
    assert (tersimpan.status, tersimpan.jumlah_jawaban) == (StatusSesiEir.BERJALAN, 1)


def test_eir_tanpa_llm_membalas_503(client, sesi, pakai_llm):
    pakai_llm(None)
    assert _pesan(client, sesi).status_code == 503


def test_pertanyaan_terlarang_diganti_panduan(client, sesi, pakai_llm):
    pakai_llm(LlmUji(pertanyaan="Kemungkinan besar ini maag, sebaiknya minum obat."))
    pesan = _pesan(client, sesi).get_json()["pesan"]
    assert "maag" not in pesan
    assert pesan.endswith("?")


def test_ringkasan_otomatis_setelah_lima_belas_jawaban(client, sesi):
    # Keputusan E6. LlmTiruan baru menandai cukup setelah tujuh jawaban, jadi sesi berakhir di jawaban ketujuh;
    # batas 15 diuji dengan menaikkan minimum supaya tanda cukup diabaikan.
    for i in range(6):
        isi = _pesan(client, sesi, f"jawaban {i}").get_json()
        assert isi["status"] == "berjalan"
    isi = _pesan(client, sesi, "jawaban ketujuh").get_json()
    assert (isi["status"], isi["pesan"], isi["jumlah_jawaban"]) == ("selesai", PENUTUP, 7)


def test_batas_lima_belas_jawaban(app, client, sesi, monkeypatch):
    monkeypatch.setitem(app.config, "EIR_MIN_JAWABAN", 99)
    for i in range(14):
        assert _pesan(client, sesi, f"jawaban {i}").get_json()["status"] == "berjalan"
    isi = _pesan(client, sesi, "jawaban kelima belas").get_json()
    assert (isi["status"], isi["jumlah_jawaban"]) == ("selesai", 15)


def test_jawaban_kelima_belas_saat_groq_mati_lalu_selesai(app, client, sesi, monkeypatch, pakai_llm):
    monkeypatch.setitem(app.config, "EIR_MIN_JAWABAN", 99)
    for i in range(14):
        _pesan(client, sesi, f"jawaban {i}")
    pakai_llm(LlmUji(gagal=True))
    assert _pesan(client, sesi, "jawaban kelima belas").status_code == 503
    respons = _pesan(client, sesi, "jawaban keenam belas")
    assert respons.status_code == 409
    assert "Tekan Selesai" in respons.get_json()["detail"]


@pytest.mark.parametrize(
    ("header", "pesan"),
    [({}, "X-Token-Eir wajib"), ({"X-Token-Eir": "rusak"}, "tidak dikenali")],
)
def test_pesan_tanpa_token_valid(client, sesi, header, pesan):
    respons = _pesan(client, (sesi[0], header))
    assert respons.status_code == 401
    assert pesan in respons.get_json()["detail"]


def test_token_sesi_lain_ditolak(client, perawat, kunjungan_hijau, sesi):
    token = _tautan(client, perawat, kunjungan_hijau).get_json()["token"]
    sesi_lain = _buka(client, token).get_json()
    respons = _pesan(client, (sesi[0], {"X-Token-Eir": sesi_lain["token_sesi"]}))
    assert respons.status_code == 401


def test_sesi_tidak_ditemukan(app, client):
    from app.ai.eir.tautan import TokenSesiEir

    id_sesi = uuid.uuid4()
    token = TokenSesiEir(app.config["SECRET_KEY"], 7200).buat(id_sesi)
    assert _pesan(client, (str(id_sesi), {"X-Token-Eir": token})).status_code == 404


def test_pesan_ditolak_bila_pasien_sudah_dipanggil(client, sesi, kunjungan_hijau, sesi_db):
    kunjungan_hijau.status = StatusKunjungan.DITANGANI
    sesi_db.commit()
    respons = _pesan(client, sesi)
    assert respons.status_code == 409
    assert "sudah dipanggil" in respons.get_json()["detail"]


def test_batas_pesan_per_menit(app, client, sesi, monkeypatch):
    # Desain 7.2: 20 pesan per menit per sesi. Batasnya diperkecil supaya tes cepat.
    monkeypatch.setitem(app.config, "BATAS_PESAN_EIR", "2 per 1 minute")
    assert [_pesan(client, sesi, f"jawaban {i}").status_code for i in range(2)] == [200, 200]
    respons = _pesan(client, sesi)
    assert respons.status_code == 429
    assert int(respons.headers["Retry-After"]) >= 1
    assert _suara(client, sesi).status_code == 429
    assert _ambil_sesi(sesi[0]).jumlah_jawaban == 2


def test_pembatas_pesan_mati_bila_limiter_nonaktif(app, client, sesi, monkeypatch):
    from app.extensions import limiter

    monkeypatch.setitem(app.config, "BATAS_PESAN_EIR", "1 per 1 minute")
    monkeypatch.setattr(limiter, "enabled", False)
    assert [_pesan(client, sesi, f"jawaban {i}").status_code for i in range(2)] == [200, 200]


def test_pesan_kosong_ditolak(client, sesi):
    respons = _pesan(client, sesi, "   ")
    assert respons.status_code == 422
    assert respons.get_json()["errors"][0] == {"field": "teks", "pesan": "Pesan wajib diisi."}


# ---------------------------------------------------------------- selesai


def test_selesai_butuh_tujuh_jawaban(client, sesi):
    _pesan(client, sesi)
    respons = _selesai(client, sesi)
    assert respons.status_code == 409
    assert respons.get_json()["jumlah_jawaban"] == 1


def test_selesai_membuat_ringkasan_untuk_perawat(app, client, sesi, monkeypatch, masuk):
    # SKPL TC-15: ringkasan masuk ke data pasien dan menunggu pemeriksaan perawat.
    monkeypatch.setitem(app.config, "EIR_MIN_JAWABAN", 2)
    _pesan(client, sesi, "perut sakit sejak semalam")
    _pesan(client, sesi, "nyerinya di kanan bawah")
    respons = _selesai(client, sesi)
    assert respons.status_code == 200
    assert (respons.get_json()["status"], respons.get_json()["pesan"]) == ("selesai", PENUTUP)
    assert _selesai(client, sesi).status_code == 409

    tersimpan = _ambil_sesi(sesi[0])
    ringkasan = client.get(
        f"/api/v1/kunjungan/{tersimpan.id_kunjungan}/ringkasan-eir", headers=masuk(Peran.PERAWAT)[1]
    ).get_json()
    assert ringkasan["status"] == "selesai"
    assert ringkasan["ringkasan"]["keluhan_utama"] == "perut sakit sejak semalam"
    assert ringkasan["ringkasan"]["kategori_keluhan"] == "Lainnya"
    assert [i["peran"] for i in ringkasan["transkrip"]] == ["eir", "pengisi", "eir", "pengisi", "eir", "eir"]


def test_selesai_saat_groq_mati(app, client, sesi, monkeypatch, pakai_llm):
    monkeypatch.setitem(app.config, "EIR_MIN_JAWABAN", 1)
    _pesan(client, sesi)
    pakai_llm(LlmUji(gagal=True))
    assert _selesai(client, sesi).status_code == 503
    assert _ambil_sesi(sesi[0]).status == StatusSesiEir.BERJALAN


def test_selesai_tanpa_token(client, sesi):
    assert _selesai(client, (sesi[0], {})).status_code == 401


# ---------------------------------------------------------------- suara


def test_suara_diubah_ke_teks_lalu_diproses(client, sesi, llm):
    respons = _suara(client, sesi)
    assert respons.status_code == 200
    isi = respons.get_json()
    assert (isi["transkripsi"], isi["jumlah_jawaban"]) == ("pusing sejak pagi", 1)
    assert llm.audio == [(AUDIO_WEBM, "rekaman.webm")]
    assert _ambil_sesi(sesi[0]).transkrip[1]["teks"] == "pusing sejak pagi"


def test_suara_dengan_tanda_bahaya(client, sesi, pakai_llm):
    pakai_llm(LlmUji(teks_suara="bapak saya tiba-tiba bicaranya pelo"))
    assert _suara(client, sesi).get_json()["status"] == "dihentikan"


@pytest.mark.parametrize(
    ("data", "pesan"),
    [
        (b"", "Rekaman kosong."),
        (b"bukan audio sama sekali", "Rekaman harus berformat webm, ogg, mp3, m4a, atau wav."),
    ],
)
def test_suara_tidak_valid(client, sesi, data, pesan):
    respons = _suara(client, sesi, data)
    assert respons.status_code == 422
    assert respons.get_json()["errors"] == [{"field": "berkas", "pesan": pesan}]


def test_suara_terlalu_besar(app, client, sesi, monkeypatch):
    monkeypatch.setitem(app.config, "UKURAN_MAKS_SUARA", 32)
    respons = _suara(client, sesi)
    assert respons.status_code == 422
    assert respons.get_json()["errors"][0]["pesan"] == "Ukuran rekaman maksimal 0 MB."


def test_suara_melebihi_batas_request(app, client, sesi, monkeypatch):
    monkeypatch.setitem(app.config, "UKURAN_MAKS_REQUEST_SUARA", 100)
    assert _suara(client, sesi, AUDIO_WEBM * 4).status_code == 413


def test_suara_tanpa_berkas(client, sesi):
    respons = _suara(client, sesi, None)
    assert respons.status_code == 422
    assert respons.get_json()["errors"][0]["field"] == "berkas"


def test_suara_bukan_berkas_ditolak(client, sesi):
    from app.services.eir_service import EirService

    with pytest.raises(ValidasiGagalError) as galat:
        EirService._baca_audio("bukan berkas")
    assert galat.value.errors == [{"field": "berkas", "pesan": "Rekaman harus dikirim sebagai berkas."}]


@pytest.mark.parametrize(
    ("llm_uji", "kode"),
    [(None, 503), (LlmUji(gagal_suara=True), 503), (LlmUji(teks_suara=""), 422)],
)
def test_suara_gagal_diubah(client, sesi, pakai_llm, llm_uji, kode):
    pakai_llm(llm_uji)
    respons = _suara(client, sesi)
    assert respons.status_code == kode
    assert _ambil_sesi(sesi[0]).jumlah_jawaban == 0


def test_suara_untuk_sesi_yang_berakhir_tidak_dikirim_ke_groq(client, sesi, llm):
    _pesan(client, sesi, "anak saya kejang")
    assert _suara(client, sesi).status_code == 409
    assert llm.audio == []


@pytest.mark.parametrize(
    ("awal", "jenis"),
    [
        (b"\x1aE\xdf\xa3", "webm"),
        (b"OggS", "ogg"),
        (b"RIFF\x00\x00\x00\x00WAVE", "wav"),
        (b"\x00\x00\x00\x18ftypM4A ", "m4a"),
        (b"ID3\x04", "mp3"),
        (b"\xff\xfb\x90", "mp3"),
        (b"\xff", None),
        (b"PK\x03\x04", None),
    ],
)
def test_jenis_audio(awal, jenis):
    assert jenis_audio(awal) == jenis


# ---------------------------------------------------------------- ringkasan untuk perawat (keputusan E1)


def test_ringkasan_eir_untuk_dokter_dan_404(client, masuk, sesi, kunjungan_hijau, buat_kunjungan):
    _pesan(client, sesi, "dada saya seperti ditekan")
    dokter = masuk(Peran.DOKTER)[1]
    isi = client.get(f"/api/v1/kunjungan/{kunjungan_hijau.id_kunjungan}/ringkasan-eir", headers=dokter).get_json()
    assert (isi["status"], isi["ringkasan"]) == ("dihentikan", None)
    assert isi["tanda_bahaya"] == "Nyeri dada seperti ditekan atau menjalar"

    tanpa_sesi = buat_kunjungan()
    respons = client.get(f"/api/v1/kunjungan/{tanpa_sesi.id_kunjungan}/ringkasan-eir", headers=dokter)
    assert respons.status_code == 404
    assert "belum punya sesi" in respons.get_json()["detail"]
    respons = client.get(f"/api/v1/kunjungan/{uuid.uuid4()}/ringkasan-eir", headers=dokter)
    assert respons.get_json()["detail"] == "Kunjungan tidak ditemukan."


def test_ringkasan_eir_mengambil_sesi_terbaru(client, perawat, kunjungan_hijau, llm):
    token = _tautan(client, perawat, kunjungan_hijau).get_json()["token"]
    pertama = _buka(client, token).get_json()["id_sesi"]
    kedua = _buka(client, token, pengisi="keluarga").get_json()["id_sesi"]
    assert pertama != kedua
    isi = client.get(f"/api/v1/kunjungan/{kunjungan_hijau.id_kunjungan}/ringkasan-eir", headers=perawat[1]).get_json()
    assert (isi["id_sesi"], isi["pengisi"]) == (kedua, "keluarga")


def test_ringkasan_eir_ditolak_untuk_admin(client, masuk, kunjungan_hijau):
    respons = client.get(
        f"/api/v1/kunjungan/{kunjungan_hijau.id_kunjungan}/ringkasan-eir", headers=masuk(Peran.ADMIN)[1]
    )
    assert respons.status_code == 403


# ---------------------------------------------------------------- konkurensi


@pytest.mark.tanpa_rollback
def test_dua_pesan_bersamaan_tidak_saling_menimpa(app, data_nyata, buat_pengguna, monkeypatch):
    """FOR UPDATE pada sesi: dua jawaban yang datang bersamaan sama-sama tercatat di transkrip."""
    perawat = buat_pengguna(Peran.PERAWAT)
    pasien = Pasien(
        didaftarkan_oleh=perawat.id_pengguna, nama="Uji", perkiraan_usia=30, jenis_kelamin=JenisKelamin.LAKI_LAKI
    )
    db.session.add(pasien)
    db.session.flush()
    kunjungan = Kunjungan(id_pasien=pasien.id_pasien)
    db.session.add(kunjungan)
    db.session.flush()
    sesi = SesiEir(
        id_kunjungan=kunjungan.id_kunjungan, pengisi=PengisiEir.PASIEN, waktu_persetujuan=db.func.now(), transkrip=[]
    )
    db.session.add(sesi)
    db.session.commit()
    id_sesi = sesi.id_sesi
    db.session.remove()

    from app.ai.eir.tautan import TokenSesiEir

    token = TokenSesiEir(app.config["SECRET_KEY"], 7200).buat(id_sesi)
    bertemu = threading.Barrier(2, timeout=1)

    class LlmLambat(LlmUji):
        def chat(self, pesan, skema, nama_skema):
            # Tanpa kunci baris, kedua request sampai di sini bersamaan dengan transkrip lama, sehingga salah satu
            # jawaban hilang saat commit. Dengan kunci, request kedua tertahan dan yang pertama lanjut setelah 1 detik.
            with contextlib.suppress(threading.BrokenBarrierError):
                bertemu.wait()
            return super().chat(pesan, skema, nama_skema)

    monkeypatch.setattr(app.extensions["model_registry"], "llm", LlmLambat())
    hasil: list[int] = []

    def kirim(teks):
        with app.app_context():
            respons = app.test_client().post(
                f"/api/v1/eir/sesi/{id_sesi}/pesan", json={"teks": teks}, headers={"X-Token-Eir": token}
            )
            hasil.append(respons.status_code)
            db.session.remove()

    utas = [threading.Thread(target=kirim, args=(f"jawaban {i}",)) for i in range(2)]
    for u in utas:
        u.start()
    for u in utas:
        u.join()
    assert hasil == [200, 200]
    with app.app_context():
        tersimpan = db.session.get(SesiEir, id_sesi)
        assert tersimpan.jumlah_jawaban == 2
        db.session.remove()
