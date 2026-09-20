import "server-only";
import type { DokterRujukan, RiskLevel, TriageInput } from "@/lib/schemas/triase.schema";

interface RosterEntry {
  poli: string;
  dokter: DokterRujukan;
}

const IGD: RosterEntry = {
  poli: "IGD (Instalasi Gawat Darurat)",
  dokter: { nama: "dr. Agus Prasetyo", jenis: "umum" },
};
const POLI_JANTUNG: RosterEntry = {
  poli: "Poli Jantung (Kardiologi)",
  dokter: { nama: "dr. Bagus Kurniawan, Sp.JP", jenis: "spesialis", spesialisasi: "Kardiologi" },
};
const POLI_PARU: RosterEntry = {
  poli: "Poli Paru",
  dokter: { nama: "dr. Yuni Kristiani, Sp.P", jenis: "spesialis", spesialisasi: "Paru" },
};
const POLI_ANAK: RosterEntry = {
  poli: "Poli Anak",
  dokter: { nama: "dr. Hendra Saputra, Sp.A", jenis: "spesialis", spesialisasi: "Anak" },
};
const POLI_PENYAKIT_DALAM: RosterEntry = {
  poli: "Poli Penyakit Dalam",
  dokter: { nama: "dr. Made Wirawan, Sp.PD", jenis: "spesialis", spesialisasi: "Penyakit Dalam" },
};
const POLI_UMUM: RosterEntry = {
  poli: "Poli Umum",
  dokter: { nama: "dr. Fitri Handayani", jenis: "umum" },
};

export function assignPoliDanDokter(
  input: TriageInput,
  riskLevel: RiskLevel,
): { poliTujuan: string; dokterRujukan: DokterRujukan } {
  const teks = `${input.keluhanUtama} ${input.gejala}`.toLowerCase();

  let entry: RosterEntry;
  if (riskLevel === "kritis") {
    entry = IGD;
  } else if (/dada|jantung|berdebar|palpitasi/.test(teks)) {
    entry = POLI_JANTUNG;
  } else if (/napas|paru|batuk|sesak|dahak/.test(teks)) {
    entry = POLI_PARU;
  } else if (/anak|balita|bayi/.test(teks)) {
    entry = POLI_ANAK;
  } else if (riskLevel === "tinggi" || riskLevel === "sedang") {
    entry = POLI_PENYAKIT_DALAM;
  } else {
    entry = POLI_UMUM;
  }

  return { poliTujuan: entry.poli, dokterRujukan: entry.dokter };
}
