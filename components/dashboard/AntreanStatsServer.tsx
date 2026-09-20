import { Card } from "@/components/ui/card";
import { getAntreanStats } from "@/lib/data/stats";

/**
 * AntreanStatsServer - async Server Component (Modul 6, Bab C & E). Tidak
 * ada "use client" sama sekali: data diambil langsung dengan await di dalam
 * komponen, tanpa useState/useEffect. Zero JavaScript untuk panel ini
 * dikirim ke browser — murni HTML yang di-stream begitu data siap.
 */
export async function AntreanStatsServer() {
  const stats = await getAntreanStats();

  const items: Array<{ label: string; value: number; tone: string }> = [
    { label: "Total Antrean", value: stats.total, tone: "text-slate-900 dark:text-slate-200" },
    { label: "Kritis", value: stats.perLevel.kritis, tone: "text-red-600 dark:text-red-400" },
    { label: "Tinggi", value: stats.perLevel.tinggi, tone: "text-orange-600 dark:text-orange-400" },
    { label: "Sedang", value: stats.perLevel.sedang, tone: "text-amber-600 dark:text-amber-400" },
    { label: "Rendah", value: stats.perLevel.rendah, tone: "text-emerald-600 dark:text-emerald-400" },
  ];

  return (
    <section className="grid grid-cols-2 md:grid-cols-5 gap-3" aria-label="Ringkasan statistik antrean">
      {items.map((item) => (
        <Card key={item.label} padding="compact" className="text-center py-3">
          <p className={`text-2xl font-bold ${item.tone}`}>{item.value}</p>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{item.label}</p>
        </Card>
      ))}
    </section>
  );
}
