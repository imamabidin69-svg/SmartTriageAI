"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { RiskBadge } from "@/components/ui/risk-badge";
import { fetchRiwayatTriase } from "@/lib/api-client";

function formatWaktu(iso: string): string {
  try {
    return new Date(iso).toLocaleString("id-ID", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export function RiwayatTriaseClient() {
  const searchParams = useSearchParams();
  const [namaInput, setNamaInput] = useState(searchParams.get("nama") ?? "");
  const [searchNama, setSearchNama] = useState(searchParams.get("nama") ?? "");

  useEffect(() => {
    const fromUrl = searchParams.get("nama");
    if (fromUrl) {
      setNamaInput(fromUrl);
      setSearchNama(fromUrl);
    }
  }, [searchParams]);

  const { data, isFetching, isError } = useQuery({
    queryKey: ["riwayat-triase", searchNama],
    queryFn: () => fetchRiwayatTriase(searchNama),
    enabled: searchNama.length > 0,
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900 dark:text-slate-200">Riwayat Triase Pasien</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Cari nama pasien untuk melihat seluruh riwayat kunjungan triase sebelumnya.
        </p>
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          setSearchNama(namaInput);
        }}
        className="flex flex-wrap gap-2"
      >
        <input
          type="search"
          value={namaInput}
          onChange={(e) => setNamaInput(e.target.value)}
          placeholder="Nama pasien…"
          aria-label="Cari nama pasien"
          className="flex-1 min-w-[200px] px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-sm bg-white dark:bg-slate-900 dark:text-slate-200"
        />
        <button
          type="submit"
          className="px-4 py-2 rounded-md bg-blue-600 text-white text-sm font-medium hover:bg-blue-700"
        >
          Cari
        </button>
      </form>

      {searchNama.length === 0 && (
        <p className="text-sm text-slate-500 dark:text-slate-400">Masukkan nama pasien untuk memulai pencarian.</p>
      )}

      {isFetching && <p className="text-sm text-slate-500 dark:text-slate-400">Mencari…</p>}

      {isError && (
        <div
          className="rounded-lg border border-red-200 bg-red-50 dark:bg-red-950/30 p-4 text-red-800 dark:text-red-300"
          role="alert"
        >
          Gagal memuat riwayat triase.
        </div>
      )}

      {data && data.length === 0 && searchNama.length > 0 && !isFetching && (
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Tidak ditemukan riwayat untuk &quot;{searchNama}&quot;.
        </p>
      )}

      {data && data.length > 0 && (
        <div className="space-y-3">
          {data.map((r) => (
            <Card key={r.idTriase} emphasis="hoverable">
              <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                <h3 className="font-bold text-slate-900 dark:text-slate-200">{r.namaPasien}</h3>
                <RiskBadge level={r.riskLevel} />
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-1">{r.keluhanUtama}</p>
              <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500 dark:text-slate-400">
                <span>
                  {formatWaktu(r.waktuTriase)} &middot; {r.poliTujuan}
                </span>
                <Link
                  href={`/triase/${r.idTriase}`}
                  className="text-blue-600 dark:text-blue-400 hover:underline font-medium"
                >
                  Lihat Detail →
                </Link>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
