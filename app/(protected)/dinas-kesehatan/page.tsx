import type { Metadata } from "next";
import { Card } from "@/components/ui/card";
import { ExportButtons } from "@/components/ui/export-buttons";
import { fetchRingkasanRegionalServer } from "@/lib/server-api";
import { getSession } from "@/lib/session";

export const metadata: Metadata = {
  title: "Laporan Regional",
  description: "Ringkasan agregat data triase lintas-faskes untuk pengawasan Dinas Kesehatan.",
};

export default async function DinasKesehatanPage() {
  const session = await getSession();

  if (session?.role !== "dinas_kesehatan") {
    return (
      <div
        className="max-w-3xl rounded-lg border border-amber-300 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/30 p-6"
        role="alert"
      >
        <h1 className="text-lg font-bold text-amber-900 dark:text-amber-300 mb-2">Akses Tidak Diizinkan</h1>
        <p className="text-sm text-amber-800 dark:text-amber-200">Halaman ini khusus untuk Dinas Kesehatan.</p>
      </div>
    );
  }

  const ringkasan = await fetchRingkasanRegionalServer();
  const totalRegional = ringkasan.reduce((sum, f) => sum + f.totalTriase, 0);
  const totalKritisRegional = ringkasan.reduce((sum, f) => sum + (f.perLevel.kritis ?? 0), 0);

  const csvHeaders = ["Faskes", "Total Triase", "Kritis", "Tinggi", "Sedang", "Rendah"];
  const csvRows = ringkasan.map((f) => [
    f.faskesNama,
    String(f.totalTriase),
    String(f.perLevel.kritis ?? 0),
    String(f.perLevel.tinggi ?? 0),
    String(f.perLevel.sedang ?? 0),
    String(f.perLevel.rendah ?? 0),
  ]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-200">Laporan Regional</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Ringkasan agregat data triase lintas-faskes (read-only, akses eksternal).
          </p>
        </div>
        <ExportButtons filenamePrefix="laporan-regional" headers={csvHeaders} rows={csvRows} />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <Card padding="compact" className="text-center py-4">
          <p className="text-3xl font-bold text-slate-900 dark:text-slate-200">{totalRegional}</p>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Total Triase Regional</p>
        </Card>
        <Card padding="compact" className="text-center py-4">
          <p className="text-3xl font-bold text-red-600 dark:text-red-400">{totalKritisRegional}</p>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Total Kasus Kritis</p>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {ringkasan.map((f) => (
          <Card key={f.faskesId} emphasis="hoverable">
            <h2 className="font-bold text-slate-900 dark:text-slate-200 mb-3">{f.faskesNama}</h2>
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-2">Total triase: {f.totalTriase}</p>
            <dl className="grid grid-cols-4 gap-2 text-center">
              {Object.entries(f.perLevel).map(([level, count]) => (
                <div key={level}>
                  <dd className="text-lg font-bold text-slate-900 dark:text-slate-200">{count}</dd>
                  <dt className="text-xs text-slate-500 dark:text-slate-400 capitalize">{level}</dt>
                </div>
              ))}
            </dl>
          </Card>
        ))}
      </div>
    </div>
  );
}
