import { dehydrate, HydrationBoundary } from "@tanstack/react-query";
import type { Metadata } from "next";
import { KonfigurasiAiFormClient } from "@/components/superadmin/KonfigurasiAiFormClient";
import { aiConfigKey } from "@/hooks/useAiConfigQueries";
import { getQueryClient } from "@/lib/query-client";
import { fetchAiConfigServer } from "@/lib/server-api";
import { getSession } from "@/lib/session";

export const metadata: Metadata = {
  title: "Konfigurasi Model AI",
  description: "Pengaturan ambang batas dan versi model klasifikasi AI lintas-faskes.",
};

export default async function KonfigurasiAiPage() {
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

  const queryClient = getQueryClient();
  await queryClient.prefetchQuery({ queryKey: aiConfigKey(), queryFn: fetchAiConfigServer });

  return (
    <div>
      <h1 className="text-xl font-bold text-slate-900 dark:text-slate-200 mb-1">Konfigurasi Model AI</h1>
      <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">
        Atur versi model dan ambang batas klasifikasi yang berlaku di seluruh faskes.
      </p>
      <HydrationBoundary state={dehydrate(queryClient)}>
        <KonfigurasiAiFormClient />
      </HydrationBoundary>
    </div>
  );
}
