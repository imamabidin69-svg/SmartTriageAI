import type { Metadata } from "next";
import { Card } from "@/components/ui/card";
import { ExportButtons } from "@/components/ui/export-buttons";
import { fetchAntreanServer } from "@/lib/server-api";
import { getSession } from "@/lib/session";

export const metadata: Metadata = {
  title: "Laporan & Statistik",
  description: "Ringkasan agregat data triase di faskes Anda.",
};

export default async function LaporanPage() {
  const session = await getSession();

  if (session?.role !== "admin_faskes") {
    return (
      <div
        className="max-w-3xl rounded-lg border border-amber-300 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/30 p-6"
        role="alert"
      >
        <h1 className="text-lg font-bold text-amber-900 dark:text-amber-300 mb-2">Akses Tidak Diizinkan</h1>
        <p className="text-sm text-amber-800 dark:text-amber-200">Halaman ini khusus untuk Admin Faskes.</p>
      </div>
    );
  }

  const records = await fetchAntreanServer();

  const perLevel: Record<string, number> = { kritis: 0, tinggi: 0, sedang: 0, rendah: 0 };
  const perStatus: Record<string, number> = { menunggu: 0, disetujui: 0, menunggu_review_dokter: 0, dikoreksi: 0 };
  const perPoli: Record<string, number> = {};

  for (const r of records) {
    perLevel[r.riskLevel] = (perLevel[r.riskLevel] ?? 0) + 1;
    perStatus[r.statusValidasi] = (perStatus[r.statusValidasi] ?? 0) + 1;
    perPoli[r.poliTujuan] = (perPoli[r.poliTujuan] ?? 0) + 1;
  }

  const totalDikoreksi = perStatus.dikoreksi ?? 0;
  const tingkatKoreksi = records.length > 0 ? Math.round((totalDikoreksi / records.length) * 100) : 0;

  const STATUS_LABEL: Record<string, string> = {
    menunggu: "Menunggu Validasi",
    disetujui: "Disetujui",
    menunggu_review_dokter: "Menunggu Review Dokter",
    dikoreksi: "Dikoreksi DPJ",
  };

  const csvHeaders = [
    "Nama Pasien",
    "Keluhan Utama",
    "Risk Level",
    "Status Validasi",
    "Poli Tujuan",
    "Dokter Rujukan",
    "Dibuat Oleh",
    "Waktu Triase",
  ];
  const csvRows = records.map((r) => [
    r.namaPasien,
    r.keluhanUtama,
    r.riskLevel,
    STATUS_LABEL[r.statusValidasi] ?? r.statusValidasi,
    r.poliTujuan,
    r.dokterRujukan.nama,
    r.dibuatOlehNama,
    new Date(r.waktuTriase).toLocaleString("id-ID"),
  ]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-200">Laporan &amp; Statistik</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Ringkasan agregat data triase di {session.faskesNama}.
          </p>
        </div>
        <ExportButtons
          filenamePrefix={`laporan-triase-${session.faskesNama.toLowerCase().replace(/\s+/g, "-")}`}
          headers={csvHeaders}
          rows={csvRows}
        />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Card padding="compact" className="text-center py-4">
          <p className="text-3xl font-bold text-slate-900 dark:text-slate-200">{records.length}</p>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Total Triase Tercatat</p>
        </Card>
        <Card padding="compact" className="text-center py-4">
          <p className="text-3xl font-bold text-red-600 dark:text-red-400">{perLevel.kritis}</p>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Kasus Kritis</p>
        </Card>
        <Card padding="compact" className="text-center py-4">
          <p className="text-3xl font-bold text-emerald-600 dark:text-emerald-400">{perStatus.disetujui ?? 0}</p>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Sudah Disetujui</p>
        </Card>
        <Card padding="compact" className="text-center py-4">
          <p className="text-3xl font-bold text-amber-600 dark:text-amber-400">{tingkatKoreksi}%</p>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Tingkat Koreksi DPJ</p>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <h2 className="font-semibold text-slate-800 dark:text-slate-200 mb-3">Distribusi Tingkat Kegawatan</h2>
          <dl className="space-y-2">
            {Object.entries(perLevel).map(([level, count]) => (
              <div key={level} className="flex items-center justify-between text-sm">
                <dt className="text-slate-600 dark:text-slate-400 capitalize">{level}</dt>
                <dd className="font-medium text-slate-900 dark:text-slate-200">{count}</dd>
              </div>
            ))}
          </dl>
        </Card>

        <Card>
          <h2 className="font-semibold text-slate-800 dark:text-slate-200 mb-3">Status Validasi</h2>
          <dl className="space-y-2">
            {Object.entries(perStatus).map(([status, count]) => (
              <div key={status} className="flex items-center justify-between text-sm">
                <dt className="text-slate-600 dark:text-slate-400">{STATUS_LABEL[status] ?? status}</dt>
                <dd className="font-medium text-slate-900 dark:text-slate-200">{count}</dd>
              </div>
            ))}
          </dl>
        </Card>

        <Card className="md:col-span-2">
          <h2 className="font-semibold text-slate-800 dark:text-slate-200 mb-3">Rujukan per Poli</h2>
          {Object.keys(perPoli).length === 0 ? (
            <p className="text-sm text-slate-500 dark:text-slate-400">Belum ada data.</p>
          ) : (
            <dl className="space-y-2">
              {Object.entries(perPoli)
                .sort((a, b) => b[1] - a[1])
                .map(([poli, count]) => (
                  <div key={poli} className="flex items-center justify-between text-sm">
                    <dt className="text-slate-600 dark:text-slate-400">{poli}</dt>
                    <dd className="font-medium text-slate-900 dark:text-slate-200">{count}</dd>
                  </div>
                ))}
            </dl>
          )}
        </Card>
      </div>
    </div>
  );
}
