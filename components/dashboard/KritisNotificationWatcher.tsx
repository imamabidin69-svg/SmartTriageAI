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
