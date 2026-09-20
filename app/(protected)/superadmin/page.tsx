import type { Metadata } from "next";
import { Card } from "@/components/ui/card";
import { fetchFaskesRingkasanServer } from "@/lib/server-api";
import { getSession } from "@/lib/session";

export const metadata: Metadata = {
  title: "Kelola Faskes",
  description: "Ringkasan seluruh fasilitas kesehatan yang terdaftar di sistem.",
};

export default async function SuperAdminPage() {
  const session = await getSession();

  if (session?.role !== "super_admin") {
    return (
      <div
        className="max-w-3xl rounded-lg border border-amber-300 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/30 p-6"
        role="alert"
      >
        <h1 className="text-lg font-bold text-amber-900 dark:text-amber-300 mb-2">Akses Tidak Diizinkan</h1>
        <p className="text-sm text-amber-800 dark:text-amber-200">Halaman ini khusus untuk Super Admin.</p>
      </div>
    );
  }

  const ringkasan = await fetchFaskesRingkasanServer();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900 dark:text-slate-200">Kelola Faskes</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Ringkasan seluruh fasilitas kesehatan yang terdaftar di sistem (lintas-faskes).
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {ringkasan.map((f) => (
          <Card key={f.id} emphasis="hoverable">
            <h2 className="font-bold text-slate-900 dark:text-slate-200 mb-3">{f.nama}</h2>
            <dl className="grid grid-cols-2 gap-3">
              <div>
                <dt className="text-xs text-slate-500 dark:text-slate-400">Jumlah Staf</dt>
                <dd className="text-2xl font-bold text-slate-900 dark:text-slate-200">{f.jumlahStaf}</dd>
              </div>
              <div>
                <dt className="text-xs text-slate-500 dark:text-slate-400">Total Triase</dt>
                <dd className="text-2xl font-bold text-slate-900 dark:text-slate-200">{f.jumlahTriase}</dd>
              </div>
            </dl>
          </Card>
        ))}
      </div>
    </div>
  );
}
