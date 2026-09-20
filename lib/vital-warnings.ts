import type { VitalSigns } from "@/lib/schemas/triase.schema";

export function checkVitalWarnings(v: VitalSigns): string[] {
  const warnings: string[] = [];

  if (v.tekananDarahSistolik < 40 || v.tekananDarahSistolik > 260) {
    warnings.push(`Tekanan darah sistolik ${v.tekananDarahSistolik} mmHg tidak lazim.`);
  }
  if (v.tekananDarahDiastolik < 20 || v.tekananDarahDiastolik > 180) {
    warnings.push(`Tekanan darah diastolik ${v.tekananDarahDiastolik} mmHg tidak lazim.`);
  }
  if (v.suhuTubuh < 30 || v.suhuTubuh > 43) {
    warnings.push(`Suhu tubuh ${v.suhuTubuh}°C tidak lazim.`);
  }
  if (v.nadiPerMenit < 20 || v.nadiPerMenit > 250) {
    warnings.push(`Nadi ${v.nadiPerMenit} bpm tidak lazim.`);
  }
  if (v.lajuNapas < 5 || v.lajuNapas > 60) {
    warnings.push(`Laju napas ${v.lajuNapas}/menit tidak lazim.`);
  }

  return warnings;
}
