import { dehydrate, HydrationBoundary } from "@tanstack/react-query";
import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import { HasilTriaseClient } from "@/components/triase/HasilTriaseClient";
import { getQueryClient } from "@/lib/query-client";
import { triaseDetailKey } from "@/lib/query-keys";
import { fetchTriageByIdServer } from "@/lib/server-api";
import { canOverride, getSession } from "@/lib/session";

interface TriaseDetailPageProps {
  params: Promise<{ id: string }>;
}

/**
 * generateMetadata() - Metadata API DINAMIS (Modul 6, Bab F). Judul tab
 * browser memuat nama pasien sungguhan, diambil lewat fetchTriageByIdServer()
 * (HTTP ke /api/triase/[id] milik sendiri — lihat lib/server-fetch.ts)
 * SEBELUM halaman dirender — baik untuk SEO/keterbacaan tab maupun
 * accessibility (screen reader mengumumkan judul halaman yang bermakna).
 */
export async function generateMetadata({ params }: TriaseDetailPageProps): Promise<Metadata> {
  const { id } = await params;
  const record = await fetchTriageByIdServer(id).catch(() => null);
  return {
    title: record ? `Hasil Triase — ${record.namaPasien}` : "Hasil Triase Tidak Ditemukan",
    description: record
      ? `Hasil klasifikasi AI dan penjelasan (explainable AI) untuk pasien ${record.namaPasien}.`
      : undefined,
  };
}

export default async function TriaseDetailPage({ params }: TriaseDetailPageProps) {
  const { id } = await params;
  const session = await getSession(); // dijamin non-null oleh (protected)/layout.tsx; dibaca ulang di sini untuk memperoleh prop RBAC
  if (!session) {
    redirect("/login?auth_error=1");
  }

  const queryClient = getQueryClient();
  await queryClient.prefetchQuery({
    queryKey: triaseDetailKey(id),
    queryFn: async () => {
      const record = await fetchTriageByIdServer(id);
      if (!record) throw new Error("Data triase tidak ditemukan.");
      return record;
    },
  });

  return (
    <div className="max-w-3xl">
      <Link href="/dashboard" className="text-sm text-blue-600 dark:text-blue-400 hover:underline mb-4 inline-block">
        ← Kembali ke Dashboard Antrean
      </Link>

      <div className="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
        <HydrationBoundary state={dehydrate(queryClient)}>
          <HasilTriaseClient idTriase={id} currentUserId={session.userId} allowedOverride={canOverride(session)} />
        </HydrationBoundary>
      </div>
    </div>
  );
}
