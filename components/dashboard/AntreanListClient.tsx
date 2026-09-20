"use client";

import Link from "next/link";
import { useState } from "react";
import { Card } from "@/components/ui/card";
import { RiskBadge } from "@/components/ui/risk-badge";
import { useAntreanQuery } from "@/hooks/useTriaseQueries";
import type { TriageRecord } from "@/lib/schemas/triase.schema";
import { useUIStore } from "@/lib/store/useUIStore";

const STATUS_LABEL: Record<TriageRecord["statusValidasi"], string> = {
  menunggu: "Menunggu Validasi",
  disetujui: "Disetujui",
  menunggu_review_dokter: "Menunggu Review Dokter",
  dikoreksi: "Dikoreksi DPJ",
};

function formatWaktu(iso: string): string {
  try {
    return new Date(iso).toLocaleString("id-ID", {
      hour: "2-digit",
      minute: "2-digit",
      day: "2-digit",
      month: "short",
    });
  } catch {
    return iso;
  }
}

export function AntreanListClient() {
  const { data, isPending, isError, error, refetch, isFetching } = useAntreanQuery();
  const selectedRiskFilter = useUIStore((s) => s.selectedRiskFilter);
  const [searchTerm, setSearchTerm] = useState("");

  const filtered =
    data?.filter((r) => {
      const cocokRisk = selectedRiskFilter === "semua" || r.riskLevel === selectedRiskFilter;
      const cocokNama =
        searchTerm.trim().length === 0 || r.namaPasien.toLowerCase().includes(searchTerm.trim().toLowerCase());
      return cocokRisk && cocokNama;
    }) ?? [];

  if (isPending) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" aria-busy="true">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="animate-pulse rounded-xl border border-slate-200 dark:border-slate-700 p-5 h-36 bg-slate-100 dark:bg-slate-900"
          />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div
        className="rounded-lg border border-red-200 bg-red-50 dark:bg-red-950/30 dark:border-red-900 p-4 text-red-800 dark:text-red-300"
        role="alert"
      >
        Terjadi kesalahan: {error instanceof Error ? error.message : "Gagal memuat antrean"}
        <button type="button" onClick={() => void refetch()} className="ml-2 underline font-medium">
          Coba lagi
        </button>
      </div>
    );
  }

  return (
    <div>
      <p className="sr-only" role="status" aria-live="polite">
        {isFetching ? "Memperbarui antrean." : `Antrean diperbarui, ${filtered.length} pasien ditampilkan.`}
      </p>

      {data && data.length > 0 && (
        <input
          type="search"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Cari nama pasien di antrean…"
          aria-label="Cari nama pasien"
          className="w-full max-w-sm mb-4 px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm bg-white dark:bg-slate-900 dark:text-slate-200"
        />
      )}

      {filtered.length === 0 ? (
        <div className="text-center py-12 text-slate-500 dark:text-slate-400">
          {data && data.length > 0
            ? "Tidak ada pasien yang cocok dengan filter/pencarian ini."
            : "Belum ada pasien pada antrean triase."}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((record) => (
            <Card key={record.idTriase} emphasis={record.riskLevel === "kritis" ? "critical" : "hoverable"}>
              <div className="flex items-start justify-between gap-2 mb-2">
                <h3 className="font-bold text-slate-900 dark:text-slate-200">{record.namaPasien}</h3>
                <RiskBadge level={record.riskLevel} />
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-3 line-clamp-2">{record.keluhanUtama}</p>
              <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mb-4">
                <span>{STATUS_LABEL[record.statusValidasi]}</span>
                <span>{formatWaktu(record.waktuTriase)}</span>
              </div>
              <Link
                href={`/triase/${record.idTriase}`}
                className="inline-block text-sm font-medium text-blue-600 dark:text-blue-400 hover:underline"
                aria-label={`Lihat hasil dan penjelasan AI untuk pasien ${record.namaPasien}`}
              >
                Lihat Hasil &amp; Penjelasan AI →
              </Link>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
