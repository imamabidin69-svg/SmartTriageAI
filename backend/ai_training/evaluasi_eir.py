"""Evaluasi Eir untuk keluarga pasien ICU dengan kumpulan kalimat uji buatan sendiri.

Belum ada dataset percakapan keluarga pasien ICU berbahasa Indonesia yang terbuka, jadi kalimat di bawah disusun
dari topik anamnesis riwayat (kronologi, penyakit, obat, alergi, operasi, kebiasaan) dengan gaya bahasa sehari-hari.
Ada dua pemeriksaan:

1. Recall@3 GuidelineRetriever: panduan topik yang benar harus masuk tiga besar untuk setiap kalimat.
2. DetektorInformasiPenting: semua informasi penting harus tertangkap (recall) dan kalimat yang tidak
   mengandung informasi penting, termasuk kalimat penyangkalan, tidak boleh ditandai (presisi).

    python -m ai_training.evaluasi_eir
"""

from dataclasses import dataclass, field

from app.ai.eir.informasi_penting import DetektorInformasiPenting
from app.ai.eir.panduan import GuidelineRetriever, muat_panduan
from app.config import DIREKTORI_BACKEND
from app.models.enums import TopikAnamnesis

FOLDER_PANDUAN = DIREKTORI_BACKEND / "app" / "ai" / "artefak" / "panduan"
TARGET_RECALL_PANDUAN = 0.86
T = TopikAnamnesis

# (kalimat keluarga, topik yang seharusnya, kode informasi penting yang seharusnya tertangkap)
KALIMAT_UJI: tuple[tuple[str, TopikAnamnesis, frozenset[str]], ...] = (
    ("Kemarin sore bapak tiba-tiba sesak lalu pingsan di kamar mandi", T.KRONOLOGI, frozenset()),
    ("Awalnya demam tiga hari, terus muntah-muntah, baru dibawa ke IGD tadi malam", T.KRONOLOGI, frozenset()),
    ("Ibu jatuh di rumah terus tidak bisa dibangunkan", T.KRONOLOGI, frozenset()),
    ("Sebelumnya sudah berobat ke klinik dekat rumah tapi tidak membaik", T.KRONOLOGI, frozenset()),
    ("Bapak kecelakaan motor waktu pulang kerja", T.KRONOLOGI, frozenset()),
    ("Bapak punya darah tinggi sudah sepuluh tahun", T.RIWAYAT_PENYAKIT, frozenset()),
    ("Ibu kencing manis, gula darahnya sering tinggi", T.RIWAYAT_PENYAKIT, frozenset()),
    ("Dulu pernah stroke ringan dua tahun lalu", T.RIWAYAT_PENYAKIT, frozenset()),
    ("Ginjalnya sudah rusak, rutin cuci darah seminggu dua kali", T.RIWAYAT_PENYAKIT, frozenset()),
    ("Pernah sakit TBC dan minum obat enam bulan", T.RIWAYAT_PENYAKIT, frozenset({"penyakit_menular"})),
    ("Ada asma sejak kecil", T.RIWAYAT_PENYAKIT, frozenset()),
    ("Minum amlodipin sama metformin setiap pagi", T.OBAT_RUTIN, frozenset()),
    ("Bapak rutin minum warfarin dari dokter jantung", T.OBAT_RUTIN, frozenset({"pengencer_darah"})),
    ("Ibu pakai suntik insulin sebelum makan malam", T.OBAT_RUTIN, frozenset({"insulin"})),
    ("Terakhir minum obatnya kemarin pagi", T.OBAT_RUTIN, frozenset()),
    ("Suka minum jamu herbal dari pasar", T.OBAT_RUTIN, frozenset()),
    ("Bapak alergi amoxicillin, dulu badannya bentol semua", T.ALERGI, frozenset({"alergi_obat"})),
    ("Kalau makan udang langsung gatal, alergi seafood", T.ALERGI, frozenset({"alergi_lain"})),
    ("Tidak ada alergi obat setahu saya", T.ALERGI, frozenset()),
    ("Pernah disuntik antibiotik langsung sesak", T.ALERGI, frozenset({"alergi_obat"})),
    ("Alergi plester, kulitnya merah kalau ditempel", T.ALERGI, frozenset({"alergi_lain"})),
    ("Pernah operasi usus buntu tahun lalu", T.RIWAYAT_OPERASI, frozenset()),
    ("Bapak sudah pasang ring jantung dua", T.RIWAYAT_OPERASI, frozenset({"alat_implan"})),
    ("Ibu sedang hamil empat bulan", T.RIWAYAT_OPERASI, frozenset({"kehamilan"})),
    ("Dulu waktu dibius operasi lama sekali sadarnya", T.RIWAYAT_OPERASI, frozenset({"masalah_pembiusan"})),
    ("Pernah dirawat inap karena demam berdarah", T.RIWAYAT_OPERASI, frozenset()),
    ("Bapak merokok dua bungkus sehari", T.KEBIASAAN, frozenset()),
    ("Sebelum sakit masih bisa jalan sendiri dan mandi sendiri", T.KEBIASAAN, frozenset()),
    ("Nafsu makan turun, berat badan berkurang banyak", T.KEBIASAAN, frozenset()),
    (
        "Bapak pernah bilang tidak mau dipasang alat bantu napas",
        T.KEBIASAAN,
        frozenset({"keinginan_pasien"}),
    ),
)


@dataclass
class HasilEvaluasiEir:
    jumlah_kalimat: int = 0
    panduan_tepat: int = 0
    info_harapan: int = 0
    info_tertangkap: int = 0
    info_ditandai: int = 0
    meleset: list[str] = field(default_factory=list)

    @property
    def recall_panduan(self) -> float:
        return self.panduan_tepat / self.jumlah_kalimat if self.jumlah_kalimat else 0.0

    @property
    def recall_informasi(self) -> float:
        return self.info_tertangkap / self.info_harapan if self.info_harapan else 1.0

    @property
    def presisi_informasi(self) -> float:
        return self.info_tertangkap / self.info_ditandai if self.info_ditandai else 1.0

    @property
    def lulus(self) -> bool:
        return self.recall_panduan >= TARGET_RECALL_PANDUAN and self.recall_informasi == 1.0


def evaluasi(
    retriever: GuidelineRetriever,
    detektor: DetektorInformasiPenting,
    kalimat_uji: tuple[tuple[str, TopikAnamnesis, frozenset[str]], ...] = KALIMAT_UJI,
) -> HasilEvaluasiEir:
    hasil = HasilEvaluasiEir()
    for kalimat, topik, harapan in kalimat_uji:
        hasil.jumlah_kalimat += 1
        tiga_besar = [p.topik for p in retriever.cari(kalimat)]
        if topik in tiga_besar:
            hasil.panduan_tepat += 1
        else:
            hasil.meleset.append(f"Panduan {kalimat!r}: harapan {topik.value}, dapat {tiga_besar[0].value}")
        ditandai = {info.kode for info in detektor.periksa(kalimat)}
        hasil.info_harapan += len(harapan)
        hasil.info_ditandai += len(ditandai)
        hasil.info_tertangkap += len(harapan & ditandai)
        if ditandai != set(harapan):
            hasil.meleset.append(f"Informasi {kalimat!r}: harapan {sorted(harapan)}, dapat {sorted(ditandai)}")
    return hasil


if __name__ == "__main__":  # pragma: no cover
    hasil = evaluasi(GuidelineRetriever(muat_panduan(FOLDER_PANDUAN)), DetektorInformasiPenting())
    print(f"Recall@3 panduan: {hasil.recall_panduan:.2f} (target {TARGET_RECALL_PANDUAN})")
    print(f"Informasi penting: recall {hasil.recall_informasi:.2f}, presisi {hasil.presisi_informasi:.2f}")
    for baris in hasil.meleset:
        print(" -", baris)
    print("LULUS" if hasil.lulus else "BELUM LULUS")
