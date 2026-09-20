import "server-only";
import { getAiConfig } from "@/lib/data/ai-config-store";
import type { RiskLevel, TriageInput } from "@/lib/schemas/triase.schema";

export function classify(input: TriageInput): { riskLevel: RiskLevel; penjelasanAi: string } {
  const v = input.tandaVital;
  const alasan: string[] = [];
  let skor = 0;

  if (v.saturasiOksigen < 92) {
    skor += 3;
    alasan.push(`saturasi oksigen rendah (${v.saturasiOksigen}%)`);
  } else if (v.saturasiOksigen < 95) {
    skor += 1;
    alasan.push(`saturasi oksigen agak rendah (${v.saturasiOksigen}%)`);
  }

  if (v.tekananDarahSistolik >= 180 || v.tekananDarahSistolik < 90) {
    skor += 3;
    alasan.push(`tekanan darah sistolik ekstrem (${v.tekananDarahSistolik} mmHg)`);
  } else if (v.tekananDarahSistolik >= 150) {
    skor += 1;
    alasan.push(`tekanan darah sistolik tinggi (${v.tekananDarahSistolik} mmHg)`);
  }

  if (v.nadiPerMenit >= 120 || v.nadiPerMenit < 50) {
    skor += 2;
    alasan.push(`nadi tidak normal (${v.nadiPerMenit} bpm)`);
  }

  if (v.suhuTubuh >= 39) {
    skor += 2;
    alasan.push(`demam tinggi (${v.suhuTubuh}°C)`);
  } else if (v.suhuTubuh >= 37.8) {
    skor += 1;
    alasan.push(`demam ringan (${v.suhuTubuh}°C)`);
  }

  if (v.lajuNapas >= 28 || v.lajuNapas < 10) {
    skor += 2;
    alasan.push(`laju napas tidak normal (${v.lajuNapas}/menit)`);
  }

  if (/nyeri dada|sesak|tidak sadar|kejang|pendarahan hebat/i.test(input.gejala)) {
    skor += 3;
    alasan.push("terdapat kata kunci gejala berisiko tinggi pada uraian keluhan");
  }

  const { ambangKritis, ambangTinggi, ambangSedang } = getAiConfig();
  let riskLevel: RiskLevel;
  if (skor >= ambangKritis) riskLevel = "kritis";
  else if (skor >= ambangTinggi) riskLevel = "tinggi";
  else if (skor >= ambangSedang) riskLevel = "sedang";
  else riskLevel = "rendah";

  const dasar =
    alasan.length > 0
      ? `Faktor yang menjadi dasar pertimbangan: ${alasan.join(", ")}.`
      : "Seluruh tanda vital berada dalam rentang normal dan tidak ditemukan kata kunci gejala berisiko tinggi.";

  const penjelasanAi =
    `Berdasarkan data gejala "${input.keluhanUtama}" dan tanda vital yang diinput, ` +
    `sistem merekomendasikan risk level "${riskLevel.toUpperCase()}". ${dasar} ` +
    `Rekomendasi ini bersifat bantu-keputusan (explainable AI) dan wajib divalidasi oleh tenaga medis (human-in-the-loop) sebelum digunakan sebagai acuan akhir.`;

  return { riskLevel, penjelasanAi };
}
