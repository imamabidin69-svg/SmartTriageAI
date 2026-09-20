import type { Metadata } from "next";
import { Card } from "@/components/ui/card";
import { RiskBadge } from "@/components/ui/risk-badge";
import { fetchAuditLogServer } from "@/lib/server-api";
import { getSession } from "@/lib/session";

export const metadata: Metadata = {
  title: "Log Audit",
  description: "Riwayat aksi validasi triase dan manajemen akun lintas-faskes.",
};

const AKSI_LABEL: Record<string, string> = {
  setujui: "Setujui Triase",
  koreksi: "Koreksi Triase",
  ajukan_review: "Ajukan Review",
  staf_dibuat: "Staf Didaftarkan",
  staf_diedit: "Staf Diedit",
  staf_diaktifkan: "Staf Diaktifkan",
  staf_dinonaktifkan: "Staf Dinonaktifkan",
  pasien_didaftarkan: "Pasien Didaftarkan",
};

const AKSI_BADGE_COLOR: Record<string, string> = {
  setujui: "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300",
  koreksi: "bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-red-300",
  ajukan_review: "bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300",
  staf_dibuat: "bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300",
  staf_diedit: "bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300",
  staf_diaktifkan: "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300",
  staf_dinonaktifkan: "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400",
  pasien_didaftarkan: "bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300",
};

function formatWaktu(iso: string): string {
  try {
    return new Date(iso).toLocaleString("id-ID", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export default async function AuditorPage() {
  const session = await getSession();

  if (session?.role !== "auditor") {
    return (
      <div
        className="max-w-3xl rounded-lg border border-amber-300 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/30 p-6"
        role="alert"
      >
        <h1 className="text-lg font-bold text-amber-900 dark:text-amber-300 mb-2">Akses Tidak Diizinkan</h1>
        <p className="text-sm text-amber-800 dark:text-amber-200">Halaman ini khusus untuk Auditor.</p>
      </div>
    );
  }

  const log = await fetchAuditLogServer();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900 dark:text-slate-200">Log Audit</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Riwayat aksi validasi triase, manajemen akun staf, dan registrasi pasien lintas-faskes (read-only).
        </p>
      </div>

      {log.length === 0 ? (
        <p className="text-sm text-slate-500 dark:text-slate-400">Belum ada aktivitas tercatat.</p>
      ) : (
        <Card padding="none" className="overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 dark:bg-slate-900 text-left">
              <tr>
                <th className="px-4 py-3 font-semibold text-slate-700 dark:text-slate-300">Waktu</th>
                <th className="px-4 py-3 font-semibold text-slate-700 dark:text-slate-300">Faskes</th>
                <th className="px-4 py-3 font-semibold text-slate-700 dark:text-slate-300">Aksi</th>
                <th className="px-4 py-3 font-semibold text-slate-700 dark:text-slate-300">Target</th>
                <th className="px-4 py-3 font-semibold text-slate-700 dark:text-slate-300">Detail</th>
                <th className="px-4 py-3 font-semibold text-slate-700 dark:text-slate-300">Aktor</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {log.map((entry) => (
                <tr key={entry.id}>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-400 whitespace-nowrap">
                    {formatWaktu(entry.waktu)}
                  </td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{entry.faskesNama}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${AKSI_BADGE_COLOR[entry.aksi] ?? ""}`}
                    >
                      {AKSI_LABEL[entry.aksi] ?? entry.aksi}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-900 dark:text-slate-200">{entry.targetNama}</td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-400">
                    {entry.riskLevelSebelum || entry.riskLevelSesudah ? (
                      <div className="flex items-center gap-2">
                        {entry.riskLevelSebelum &&
                          entry.riskLevelSesudah &&
                          entry.riskLevelSebelum !== entry.riskLevelSesudah && (
                            <>
                              <RiskBadge level={entry.riskLevelSebelum} />
                              <span className="text-slate-400">→</span>
                            </>
                          )}
                        {entry.riskLevelSesudah && <RiskBadge level={entry.riskLevelSesudah} />}
                      </div>
                    ) : (
                      (entry.catatan ?? "-")
                    )}
                  </td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{entry.aktorNama}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
