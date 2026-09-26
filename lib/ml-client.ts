import "server-only";
import { classify } from "@/lib/classify";
import { getPasienById } from "@/lib/data/pasien-store";
import type { RiskLevel, TingkatKesadaran, TriageInput } from "@/lib/schemas/triase.schema";

const TIMEOUT_MS = 5_000;

const KODE_KESADARAN: Record<TingkatKesadaran, number> = {
  sadar_penuh: 1,
  respons_suara: 2,
  respons_nyeri: 3,
  tidak_respons: 4,
};

function hitungUsia(tanggalLahir: string | undefined): number | null {
  if (!tanggalLahir) return null;
  const lahir = new Date(tanggalLahir);
  if (Number.isNaN(lahir.getTime())) return null;
  const sekarang = new Date();
  let usia = sekarang.getFullYear() - lahir.getFullYear();
  const belumUlangTahun =
    sekarang.getMonth() < lahir.getMonth() ||
    (sekarang.getMonth() === lahir.getMonth() && sekarang.getDate() < lahir.getDate());
  if (belumUlangTahun) usia -= 1;
  return usia >= 0 ? usia : null;
}

type ResponLayananMl = {
  riskLevel: RiskLevel;
  probabilitas: Record<string, number>;
  penjelasanAi: string;
  faktorUtama: string[];
  modelVersion: string;
};

/**
 * Mengklasifikasikan input triase memakai layanan machine learning (Random
 * Forest, lihat notebooks/02_baseline.ipynb dan ml-service/app.py). Kalau
 * layanan tidak bisa dihubungi, timeout, atau mengembalikan respons yang
 * tidak valid, otomatis jatuh ke classify() berbasis aturan (lib/classify.ts)
 * supaya alur triase TIDAK PERNAH gagal total hanya karena layanan ML mati.
 */
export async function classifyWithMl(
  input: TriageInput,
): Promise<{ riskLevel: RiskLevel; penjelasanAi: string; sumber: "ml" | "aturan" }> {
  const baseUrl = process.env.ML_SERVICE_URL;
  if (!baseUrl) {
    console.warn("[ml-client] ML_SERVICE_URL belum diatur, memakai classify.ts (aturan).");
    return { ...classify(input), sumber: "aturan" };
  }

  const pasien = getPasienById(input.idPasien);
  const usia = hitungUsia(pasien?.tanggalLahir);
  const jenisKelamin = pasien?.jenisKelamin === "laki_laki" ? 2 : pasien?.jenisKelamin === "perempuan" ? 1 : null;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const respons = await fetch(`${baseUrl}/classify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: controller.signal,
      body: JSON.stringify({
        SBP: input.tandaVital.tekananDarahSistolik,
        DBP: input.tandaVital.tekananDarahDiastolik,
        HR: input.tandaVital.nadiPerMenit,
        RR: input.tandaVital.lajuNapas,
        BT: input.tandaVital.suhuTubuh,
        Saturation: input.tandaVital.saturasiOksigen,
        Age: usia,
        Sex: jenisKelamin,
        Mental: input.tingkatKesadaran ? KODE_KESADARAN[input.tingkatKesadaran] : null,
        NRS_pain: input.skalaNyeri ?? null,
        kategori_keluhan: input.kategoriKeluhan ?? null,
        gejala: input.gejala,
      }),
    });

    if (!respons.ok) {
      throw new Error(`Layanan ML mengembalikan status ${respons.status}`);
    }
    const hasil = (await respons.json()) as ResponLayananMl;
    if (!hasil.riskLevel || !hasil.penjelasanAi) {
      throw new Error("Respons layanan ML tidak lengkap");
    }
    return { riskLevel: hasil.riskLevel, penjelasanAi: hasil.penjelasanAi, sumber: "ml" };
  } catch (error) {
    const alasan = error instanceof Error ? error.message : String(error);
    console.error(`[ml-client] Gagal memanggil layanan ML (${alasan}), jatuh ke classify.ts (aturan).`);
    return { ...classify(input), sumber: "aturan" };
  } finally {
    clearTimeout(timeoutId);
  }
}
