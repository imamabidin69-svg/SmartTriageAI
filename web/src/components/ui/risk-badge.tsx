import { cva } from "class-variance-authority";
import type { RiskLevel } from "@/api/tipe";
import { LABEL_LEVEL } from "@/lib/label";

// Warna level dari prototipe (components/ui/risk-badge.tsx). Kritis berisi penuh supaya paling tegas.
const varian = cva("inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ring-1 ring-inset", {
  variants: {
    level: {
      rendah: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
      sedang: "bg-amber-50 text-amber-700 ring-amber-600/20",
      tinggi: "bg-orange-50 text-orange-700 ring-orange-600/20",
      kritis: "bg-red-700 text-white ring-red-700",
    },
  },
});

export function RiskBadge({ level }: { level: RiskLevel }) {
  return <span className={varian({ level })}>{LABEL_LEVEL[level]}</span>;
}
