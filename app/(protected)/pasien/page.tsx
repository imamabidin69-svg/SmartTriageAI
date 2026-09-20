import { dehydrate, HydrationBoundary } from "@tanstack/react-query";
import type { Metadata } from "next";
import { PasienManagementClient } from "@/components/pasien/PasienManagementClient";
import { getQueryClient } from "@/lib/query-client";
import { pasienKey } from "@/lib/query-keys";
import { fetchPasienServer } from "@/lib/server-api";
import { getSession } from "@/lib/session";

export const metadata: Metadata = {
  title: "Registrasi Pasien",
  description: "Daftarkan identitas pasien sebelum menjalani pemeriksaan triase.",
};

export default async function PasienPage() {
  const session = await getSession();

  if (session?.role !== "petugas_pendaftaran" && session?.role !== "perawat") {
    return (
      <div
        className="max-w-3xl rounded-lg border border-amber-300 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/30 p-6"
        role="alert"
      >
        <h1 className="text-lg font-bold text-amber-900 dark:text-amber-300 mb-2">Akses Tidak Diizinkan</h1>
        <p className="text-sm text-amber-800 dark:text-amber-200">
          Halaman ini khusus untuk Petugas Pendaftaran (dan Perawat untuk kondisi darurat).
        </p>
      </div>
    );
  }

  const queryClient = getQueryClient();
  await queryClient.prefetchQuery({ queryKey: pasienKey(), queryFn: fetchPasienServer });

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <PasienManagementClient showRiwayatLink={session.role === "perawat"} />
    </HydrationBoundary>
  );
}
