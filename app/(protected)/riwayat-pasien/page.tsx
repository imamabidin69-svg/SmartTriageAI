import type { Metadata } from "next";
import { Suspense } from "react";
import { RiwayatTriaseClient } from "@/components/pasien/RiwayatTriaseClient";
import { getSession } from "@/lib/session";

export const metadata: Metadata = {
  title: "Riwayat Triase Pasien",
  description: "Cari riwayat kunjungan triase pasien sebelumnya.",
};

export default async function RiwayatPasienPage() {
  const session = await getSession();

  if (session?.role !== "perawat" && session?.role !== "dokter_pj") {
    return (
      <div
        className="max-w-3xl rounded-lg border border-amber-300 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/30 p-6"
        role="alert"
      >
        <h1 className="text-lg font-bold text-amber-900 dark:text-amber-300 mb-2">Akses Tidak Diizinkan</h1>
        <p className="text-sm text-amber-800 dark:text-amber-200">
          Halaman ini khusus untuk Perawat dan Dokter Penanggung Jawab.
        </p>
      </div>
    );
  }

  return (
    <Suspense fallback={<p className="text-sm text-slate-500 dark:text-slate-400">Memuat…</p>}>
      <RiwayatTriaseClient />
    </Suspense>
  );
}
