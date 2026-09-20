import "server-only";
import type { RiskLevel } from "@/lib/schemas/triase.schema";
import { fetchAntreanServer } from "@/lib/server-api";

export interface AntreanStats {
  total: number;
  perLevel: Record<RiskLevel, number>;
  rerataUsiaTriaseMenit: number;
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function getAntreanStats(): Promise<AntreanStats> {
  await delay(1200);
  const records = await fetchAntreanServer();
  const perLevel: Record<RiskLevel, number> = { kritis: 0, tinggi: 0, sedang: 0, rendah: 0 };
  for (const r of records) perLevel[r.riskLevel] += 1;

  const now = Date.now();
  const rerataMs =
    records.length > 0
      ? records.reduce((sum, r) => sum + (now - new Date(r.waktuTriase).getTime()), 0) / records.length
      : 0;

  return {
    total: records.length,
    perLevel,
    rerataUsiaTriaseMenit: Math.round(rerataMs / 60000),
  };
}
