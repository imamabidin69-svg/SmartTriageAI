"use client";

import { type RiskFilter, useUIStore } from "@/lib/store/useUIStore";

const FILTERS: Array<{ value: RiskFilter; label: string }> = [
  { value: "semua", label: "Semua" },
  { value: "kritis", label: "Kritis" },
  { value: "tinggi", label: "Tinggi" },
  { value: "sedang", label: "Sedang" },
  { value: "rendah", label: "Rendah" },
];

export function AntreanFilterClient() {
  const selectedRiskFilter = useUIStore((s) => s.selectedRiskFilter);
  const setSelectedRiskFilter = useUIStore((s) => s.setSelectedRiskFilter);

  return (
    <fieldset className="flex flex-wrap gap-2 border-0 p-0 m-0">
      <legend className="sr-only">Filter kategori kegawatan</legend>
      {FILTERS.map((f) => {
        const isActive = selectedRiskFilter === f.value;
        return (
          <button
            key={f.value}
            type="button"
            onClick={() => setSelectedRiskFilter(f.value)}
            aria-pressed={isActive}
            className={
              isActive
                ? "px-3 py-1.5 rounded-full text-xs font-semibold bg-blue-600 text-white"
                : "px-3 py-1.5 rounded-full text-xs font-semibold bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 border border-slate-300 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700"
            }
          >
            {f.label}
          </button>
        );
      })}
    </fieldset>
  );
}
