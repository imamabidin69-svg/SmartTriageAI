import type { Metadata } from "next";
import { AsesmenVisualFormClient } from "@/components/triase/AsesmenVisualFormClient";
import { getSession } from "@/lib/session";

export const metadata: Metadata = {
  title: "Asesmen Pasien Tidak Sadar",
  description: "Asesmen visual cepat untuk pasien yang tidak dapat menyampaikan keluhan sendiri.",
};

export default async function AsesmenVisualPage() {
  const session = await getSession();

  if (session?.role !== "perawat") {
    return (
      <div
        className="max-w-3xl rounded-lg border border-amber-300 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/30 p-6"
        role="alert"
      >
        <h1 className="text-lg font-bold text-amber-900 dark:text-amber-300 mb-2">Akses Tidak Diizinkan</h1>
        <p className="text-sm text-amber-800 dark:text-amber-200">Halaman ini khusus untuk Perawat.</p>
      </div>
    );
  }

  return (
    <div className="max-w-3xl">
      <h1 className="text-xl font-bold text-slate-900 dark:text-slate-200 mb-1">Asesmen Pasien Tidak Sadar</h1>
      <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">
        Gunakan alur ini saat pasien tidak dapat menyampaikan keluhan sendiri (tidak sadar, tanpa pendamping). Catat
        observasi visual dan tanda vital — sistem akan memproses klasifikasi tingkat kegawatan berdasarkan data
        tersebut.
      </p>
      <AsesmenVisualFormClient />
    </div>
  );
}
