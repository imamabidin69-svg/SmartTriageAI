"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { useKritisWatchQuery } from "@/hooks/useTriaseQueries";
import type { TriageRecord } from "@/lib/schemas/triase.schema";

interface ToastItem {
  id: string;
  idTriase: string;
  namaPasien: string;
}

/**
 * KritisNotificationWatcher - "use client": dipasang SEKALI di
 * app/(protected)/layout.tsx (bukan cuma di halaman dashboard) supaya DPJ
 * tetap dapat notifikasi kasus kritis baru walau sedang membuka halaman
 * lain (mis. Riwayat Triase). Menutup celah FR-13 (Notifikasi Prioritas
 * Kritis) yang sejak dokumen SKPL awal ditandai "direncanakan pada
 * iterasi berikutnya" dan belum pernah benar-benar dibangun.
 *
 * Dua lapis notifikasi:
 * 1. Toast sementara (muncul ~8 detik) - HANYA untuk kasus yang BENAR-BENAR
 *    baru muncul sejak polling terakhir (bukan seluruh kasus kritis yang
 *    sudah ada dari awal sesi).
 * 2. Badge persisten di header (lihat DashboardHeaderClient) - selalu
 *    menunjukkan jumlah kasus kritis yang masih "menunggu" saat ini.
 *
 * Timer auto-dismiss diset LANGSUNG saat sebuah toast dibuat (dalam
 * addToast), bukan lewat useEffect terpisah yang memindai ulang seluruh
 * array `toasts`. Pendekatan lama (effect ber-dependency `toasts.length`)
 * berisiko memakai closure basi kalau satu toast hilang dan satu toast
 * lain masuk di render yang sama (length tetap sama, effect tidak
 * di-re-run, timer untuk toast baru tidak pernah terpasang). Timer
 * per-toast langsung menghindari kelas bug ini sama sekali.
 */
export function KritisNotificationWatcher({ enabled }: { enabled: boolean }) {
  const { data: kritisPending } = useKritisWatchQuery(enabled);
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const seenIdsRef = useRef<Set<string> | null>(null);
  const timersRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
    const timer = timersRef.current.get(id);
    if (timer) {
      clearTimeout(timer);
      timersRef.current.delete(id);
    }
  }, []);

  const addToast = useCallback(
    (item: Omit<ToastItem, "id">) => {
      const id = crypto.randomUUID();
      setToasts((prev) => [...prev, { ...item, id }]);
      timersRef.current.set(
        id,
        setTimeout(() => dismissToast(id), 8000),
      );
    },
    [dismissToast],
  );

  useEffect(() => {
    if (!kritisPending) return;

    const currentIds = new Set(kritisPending.map((r) => r.idTriase));

    // Polling pertama: catat semua yang sudah ada TANPA memunculkan toast
    // (supaya DPJ yang baru login tidak langsung dibanjiri toast untuk
    // kasus-kasus lama yang sudah menunggu sebelum ia login).
    if (seenIdsRef.current === null) {
      seenIdsRef.current = currentIds;
      return;
    }

    const baru: TriageRecord[] = kritisPending.filter((r) => !seenIdsRef.current?.has(r.idTriase));
    seenIdsRef.current = currentIds;

    for (const r of baru) {
      addToast({ idTriase: r.idTriase, namaPasien: r.namaPasien });
    }
  }, [kritisPending, addToast]);

  // Bersihkan semua timer yang masih berjalan saat komponen unmount (mis. logout).
  useEffect(() => {
    const timers = timersRef.current;
    return () => {
      for (const timer of timers.values()) clearTimeout(timer);
    };
  }, []);

  if (!enabled || toasts.length === 0) return null;

  return (
    <section
      className="fixed top-20 right-4 z-50 flex flex-col gap-2 w-80 max-w-[calc(100vw-2rem)]"
      aria-label="Notifikasi kasus kritis"
    >
      {toasts.map((t) => (
        <div
          key={t.id}
          role="alert"
          className="bg-white dark:bg-slate-800 border border-red-300 dark:border-red-800 rounded-lg shadow-lg p-4"
        >
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-start gap-2">
              <span aria-hidden="true" className="text-lg">
                🚨
              </span>
              <div>
                <p className="text-sm font-semibold text-red-700 dark:text-red-400">Kasus Kritis Baru</p>
                <p className="text-sm text-slate-700 dark:text-slate-300">{t.namaPasien}</p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => dismissToast(t.id)}
              aria-label="Tutup notifikasi"
              className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-lg leading-none"
            >
              ×
            </button>
          </div>
          <Link
            href={`/triase/${t.idTriase}`}
            onClick={() => dismissToast(t.id)}
            className="inline-block mt-2 text-sm font-medium text-blue-600 dark:text-blue-400 hover:underline"
          >
            Tinjau Sekarang →
          </Link>
        </div>
      ))}
    </section>
  );
}
