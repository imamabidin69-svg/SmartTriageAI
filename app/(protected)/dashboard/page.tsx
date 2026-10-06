import { Plus } from "@phosphor-icons/react/ssr";
import { dehydrate, HydrationBoundary } from "@tanstack/react-query";
import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { AntreanFilterClient } from "@/components/dashboard/AntreanFilterClient";
import { AntreanListClient } from "@/components/dashboard/AntreanListClient";
import { AntreanStatsServer } from "@/components/dashboard/AntreanStatsServer";
import { DpjPriorityQueueClient } from "@/components/dashboard/DpjPriorityQueueClient";
import { buttonVariants } from "@/components/ui/button";
import { getQueryClient } from "@/lib/query-client";
import { antreanKey } from "@/lib/query-keys";
import { fetchAntreanServer } from "@/lib/server-api";
import { getSession } from "@/lib/session";

export const metadata: Metadata = {
  title: "Dashboard Antrean Prioritas",
  description: "Antrean pasien tersusun otomatis berdasarkan tingkat kegawatan.",
};

export default async function DashboardPage() {
  const session = await getSession();
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
          <Link href="/triase/baru" className={buttonVariants()}>
            <Plus size={18} aria-hidden="true" />
            Input Triase
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
          className={`motion-safe:animate-pulse rounded-xl border border-slate-200 dark:border-slate-700 p-3 h-[68px] bg-slate-100 dark:bg-slate-800 ${i === 1 ? "col-span-2 md:col-span-1" : ""}`}
        />
      ))}
    </div>
  );
}
