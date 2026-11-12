"""Penyusun penjelasan penilaian: tiga faktor SHAP terbesar dan komponen NEWS2 yang menyumbang poin (FR-05).

Penjelasan dihitung dari model dan rumus NEWS2, bukan dibuat LLM. Keduanya memakai struktur Faktor yang
sama, sehingga antarmuka cukup punya satu cara menampilkan (Desain baris 257). Untuk faktor model, "naik"
berarti faktor itu menaikkan peluang perburukan (nilai SHAP positif) dan "turun" berarti menurunkannya.
Untuk komponen NEWS2, kontribusi berisi poin dan arahnya selalu "naik".
"""

from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Any

from app.models.enums import JenisKelamin

JUMLAH_FAKTOR_MODEL = 3

LABEL_JENIS_KELAMIN = {JenisKelamin.LAKI_LAKI: "laki-laki", JenisKelamin.PEREMPUAN: "perempuan"}


@dataclass(frozen=True)
class Faktor:
    """Satu faktor penjelas. `kontribusi` berisi nilai SHAP untuk model atau poin NEWS2 untuk komponen NEWS2."""

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


# Templat label dan jumlah desimal untuk setiap fitur model.
TEMPLAT_FITUR = {
    "nadi": ("Nadi {} x/menit", 1),
    "saturasi": ("Saturasi oksigen {}%", 1),
    "suhu": ("Suhu tubuh {} °C", 1),
    "td_sistolik": ("Tekanan darah sistolik {} mmHg", 1),
    "td_diastolik": ("Tekanan darah diastolik {} mmHg", 1),
    "map": ("Tekanan arteri rata-rata {} mmHg", 1),
    "laju_napas": ("Laju napas {} x/menit", 1),
    "laktat": ("Laktat {} mmol/L", 1),
    "kreatinin": ("Kreatinin {} mg/dL", 2),
    "trombosit": ("Trombosit {} ribu/µL", 1),
    "leukosit": ("Leukosit {} ribu/µL", 1),
    "bilirubin": ("Bilirubin total {} mg/dL", 1),
    "usia": ("Usia {} tahun", 1),
    "shock_index": ("Shock index {}", 2),
}


class LabelFitur:
    """Label yang dipahami tenaga medis untuk setiap fitur model, misalnya "Saturasi oksigen 88%"."""

    @staticmethod
    def label(nama: str, nilai: Any) -> str:
        if nama == "jenis_kelamin":
            return f"Jenis kelamin {LABEL_JENIS_KELAMIN[JenisKelamin(nilai)]}"
        templat, desimal = TEMPLAT_FITUR[nama]
        return templat.format(format_angka(nilai, desimal))


class PenyusunPenjelasan:
    @staticmethod
    def dari_shap(
        kontribusi: Any,
        nama_fitur_transformasi: tuple[str, ...],
        nilai_asli: dict[str, Any],
    ) -> list[Faktor]:
        """Tiga faktor dengan |SHAP| terbesar terhadap peluang perburukan.

        Fitur yang nilainya kosong lalu diisi median oleh imputer dibuang, karena itu bukan data pasien
        yang sebenarnya (misalnya hasil lab yang belum diperiksa).
        """
        kandidat: list[tuple[float, str, Any]] = []
        for i, nama in enumerate(nama_fitur_transformasi):
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
