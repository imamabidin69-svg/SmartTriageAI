import { dehydrate, HydrationBoundary } from "@tanstack/react-query";
import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { AntreanFilterClient } from "@/components/dashboard/AntreanFilterClient";
import { AntreanListClient } from "@/components/dashboard/AntreanListClient";
import { AntreanStatsServer } from "@/components/dashboard/AntreanStatsServer";
import { DpjPriorityQueueClient } from "@/components/dashboard/DpjPriorityQueueClient";
import { getQueryClient } from "@/lib/query-client";
import { antreanKey } from "@/lib/query-keys";
import { fetchAntreanServer } from "@/lib/server-api";
import { getSession } from "@/lib/session";

export const metadata: Metadata = {
  title: "Dashboard Antrean Prioritas",
  description: "Antrean pasien tersusun otomatis berdasarkan tingkat kegawatan.",
};

/**
 * app/(protected)/dashboard/page.tsx - Server Component (RSC, Modul 6 Bab C).
 * Prefetch dilakukan lewat fetchAntreanServer() (HTTP ke /api/triase sendiri
 * — lihat lib/server-fetch.ts untuk alasannya), lalu disuntikkan ke
 * QueryClient lewat prefetchQuery + dehydrate.
 *
 * Client Component turunannya (AntreanListClient) memakai useQuery dengan
 * queryKey yang SAMA PERSIS (antreanKey()) sehingga saat halaman dimuat, ia
 * langsung "melihat" cache yang sudah terisi (hydrated) tanpa loading state
 * — first paint cepat (SSR, Modul 6) DIGABUNG dengan interaktivitas penuh
 * TanStack Query untuk refetch/mutasi berikutnya (Modul 7).
 */
export default async function DashboardPage() {
  const session = await getSession(); // dijamin non-null oleh (protected)/layout.tsx
  const queryClient = getQueryClient();
  await queryClient.prefetchQuery({
    queryKey: antreanKey(),
    queryFn: fetchAntreanServer,
  });

  const isDpj = session?.role === "dokter_pj";

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-200">
            {isDpj ? "Antrean Validasi Klinis" : "Dashboard Antrean Prioritas"}
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            {isDpj
              ? "Tinjau, setujui, atau koreksi hasil klasifikasi AI untuk seluruh antrean."
              : "Antrean tersusun otomatis berdasarkan tingkat kegawatan pasien."}
          </p>
        </div>
        {session?.role === "perawat" && (
          <Link
            href="/triase/baru"
            className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            + Input Triase Baru
          </Link>
        )}
      </div>

      <Suspense fallback={<StatsSkeletonFallback />}>
        <AntreanStatsServer />
      </Suspense>

      {isDpj && (
        <HydrationBoundary state={dehydrate(queryClient)}>
          <DpjPriorityQueueClient />
        </HydrationBoundary>
      )}

      <AntreanFilterClient />

      <HydrationBoundary state={dehydrate(queryClient)}>
        <AntreanListClient />
      </HydrationBoundary>
    </div>
  );
}

function StatsSkeletonFallback() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-3" aria-hidden="true">
      {[1, 2, 3, 4, 5].map((i) => (
        <div
          key={i}
          className="animate-pulse rounded-xl border border-slate-200 dark:border-slate-700 p-3 h-[68px] bg-slate-100 dark:bg-slate-900"
        />
      ))}
    </div>
  );
}
