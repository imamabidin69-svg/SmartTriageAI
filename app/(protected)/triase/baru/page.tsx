import type { Metadata } from "next";
import { TriaseFormClient } from "@/components/triase/TriaseFormClient";
import { getSession } from "@/lib/session";

export const metadata: Metadata = {
  title: "Input Triase Baru",
  description: "Input gejala, keluhan, dan tanda vital pasien untuk diproses sistem klasifikasi AI.",
};

export default async function TriaseBaruPage() {
  const session = await getSession();

  if (session?.role !== "perawat") {
    return (
      <div
        className="max-w-3xl rounded-lg border border-amber-300 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/30 p-6"
        role="alert"
      >
        <h1 className="text-lg font-bold text-amber-900 dark:text-amber-300 mb-2">Akses Tidak Diizinkan</h1>
        <p className="text-sm text-amber-800 dark:text-amber-200">
          Hanya Perawat yang berwenang menginput gejala &amp; tanda vital pasien baru. Peran Anda saat ini tidak
          memiliki akses ke halaman ini.
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-3xl">
      <h1 className="text-xl font-bold text-slate-900 dark:text-slate-200 mb-1">Form Input Triase</h1>
      <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">
        Input gejala, keluhan, riwayat singkat, dan tanda vital pasien. Data akan diproses sistem AI untuk menghasilkan
        tingkat kegawatan beserta penjelasannya.
      </p>
      <TriaseFormClient />
    </div>
  );
}
