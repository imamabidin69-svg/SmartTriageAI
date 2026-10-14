"""Penyusun penjelasan rekomendasi: tiga faktor SHAP terbesar atau daftar aturan yang terpicu (FR-05).

Penjelasan dihitung dari model, bukan dibuat LLM. Hasil model dan hasil aturan cadangan memakai
struktur Faktor yang sama, sehingga antarmuka cukup punya satu cara menampilkan (Desain baris 257).
Arti `arah` dibaca bersama sumber_rekomendasi: untuk model, "naik" berarti faktor itu mendukung level
yang direkomendasikan (nilai SHAP positif) dan "turun" berarti melawannya; untuk aturan, "naik" berarti
menambah poin risiko.
"""

from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Any

from app.models.enums import JenisKelamin, TingkatKesadaran

JUMLAH_FAKTOR_MODEL = 3
AWALAN_KATEGORI = "kategori__kategori_keluhan_"

KETERANGAN_AVPU = {
    TingkatKesadaran.SADAR_PENUH: "sadar penuh",
    TingkatKesadaran.RESPONS_SUARA: "respons terhadap suara",
    TingkatKesadaran.RESPONS_NYERI: "respons terhadap nyeri",
    TingkatKesadaran.TIDAK_RESPONS: "tidak respons",
}
LABEL_JENIS_KELAMIN = {JenisKelamin.LAKI_LAKI: "laki-laki", JenisKelamin.PEREMPUAN: "perempuan"}


@dataclass(frozen=True)
class Faktor:
    """Satu faktor penjelas. `kontribusi` berisi nilai SHAP untuk model atau poin aturan untuk aturan cadangan."""

    fitur: str | None
    label: str
    nilai: Any
    kontribusi: float
    arah: str  # "naik", "turun", atau "netral"

    def ke_json(self) -> dict[str, Any]:
        return asdict(self)


def format_angka(nilai: float | int | Decimal, desimal: int = 1) -> str:
    """Menulis angka gaya Indonesia: 37.5 menjadi "37,5", 98.0 menjadi "98"."""
    angka = round(float(nilai), desimal)
    if angka == int(angka):
        return str(int(angka))
    return f"{angka:.{desimal}f}".rstrip("0").replace(".", ",")


class LabelFitur:
    """Label yang dipahami tenaga medis untuk setiap fitur model, misalnya "Saturasi oksigen 88%"."""

    @staticmethod
    def label(nama: str, nilai: Any) -> str:
        if nama == "kategori_keluhan":
            return f"Kategori keluhan: {nilai}"
        if nama == "Mental":
            avpu = TingkatKesadaran(nilai)
            return f"Tingkat kesadaran {avpu.value} ({KETERANGAN_AVPU[avpu]})"
        if nama == "Sex":
            return f"Jenis kelamin {LABEL_JENIS_KELAMIN[JenisKelamin(nilai)]}"
        templat = {
            "Age": "Usia {} tahun",
            "NRS_pain": "Skala nyeri {}",
            "SBP": "Tekanan darah sistolik {} mmHg",
            "DBP": "Tekanan darah diastolik {} mmHg",
            "HR": "Nadi {} x/menit",
            "RR": "Laju napas {} x/menit",
            "BT": "Suhu tubuh {} °C",
            "Saturation": "Saturasi oksigen {}%",
            "map": "Tekanan arteri rata-rata {} mmHg",
        }
        if nama == "shock_index":
            return f"Shock index {format_angka(nilai, 2)}"
        return templat[nama].format(format_angka(nilai))


class PenyusunPenjelasan:
    @staticmethod
    def dari_shap(
        kontribusi: Any,
        nama_fitur_transformasi: tuple[str, ...],
        nilai_transformasi: Any,
        nilai_asli: dict[str, Any],
    ) -> list[Faktor]:
        """Tiga faktor dengan |SHAP| terbesar untuk level yang diprediksi.

        Kolom one-hot kategori yang bernilai 0 dibuang (sama seperti prototipe), begitu juga fitur
        yang nilainya kosong lalu diisi median oleh imputer, karena itu bukan data pasien yang sebenarnya.
        """
        kandidat: list[tuple[float, str, Any]] = []
        for i, nama in enumerate(nama_fitur_transformasi):
            if nama.startswith(AWALAN_KATEGORI):
                if nilai_transformasi[i] == 0:
                    continue
                fitur, nilai = "kategori_keluhan", nama.removeprefix(AWALAN_KATEGORI)
            else:
                fitur = nama.split("__", 1)[-1]
                nilai = nilai_asli.get(fitur)
                if nilai is None:
                    continue
            kandidat.append((float(kontribusi[i]), fitur, nilai))

        kandidat.sort(key=lambda item: abs(item[0]), reverse=True)
        return [
            Faktor(
                fitur=fitur,
                label=LabelFitur.label(fitur, nilai),
                nilai=nilai,
                kontribusi=round(nilai_shap, 4),
                arah="naik" if nilai_shap > 0 else "turun",
            )
            for nilai_shap, fitur, nilai in kandidat[:JUMLAH_FAKTOR_MODEL]
        ]

    @staticmethod
    def dari_aturan(aturan_terpicu: list[Faktor]) -> list[Faktor]:
        """Semua aturan yang terpicu, diurutkan dari poin terbesar."""
        if not aturan_terpicu:
            return [
                Faktor(
                    fitur=None,
                    # Tidak mengklaim tanda vital normal: aturan cadangan tidak memeriksa, misalnya, suhu rendah
                    # atau diastolik, yang tetap bisa muncul sebagai peringatan di respons yang sama.
                    label="Tidak ada aturan risiko cadangan yang terpicu",
                    nilai=None,
                    kontribusi=0,
                    arah="netral",
                )
            ]
        return sorted(aturan_terpicu, key=lambda faktor: faktor.kontribusi, reverse=True)
