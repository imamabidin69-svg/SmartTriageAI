import { cva, type VariantProps } from "class-variance-authority";
import type { RiskLevel } from "@/lib/schemas/triase.schema";

export const riskBadgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold ring-1 ring-inset",
  {
    variants: {
      level: {
        rendah:
          "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 ring-emerald-600/20 dark:ring-emerald-400/20",
        sedang:
          "bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 ring-amber-600/20 dark:ring-amber-400/20",
        tinggi:
          "bg-orange-50 dark:bg-orange-950/40 text-orange-700 dark:text-orange-300 ring-orange-600/20 dark:ring-orange-400/20",
        kritis:
          "bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-red-300 ring-red-600/30 dark:ring-red-400/25 animate-pulse",
      },
    },
    defaultVariants: { level: "rendah" },
  },
);

const RISK_LABEL: Record<RiskLevel, string> = {
  rendah: "Rendah",
  sedang: "Sedang",
  tinggi: "Tinggi",
  kritis: "KRITIS",
};

export interface RiskBadgeProps extends VariantProps<typeof riskBadgeVariants> {
  level: RiskLevel;
}

export function RiskBadge({ level }: RiskBadgeProps) {
  return (
    <span className={riskBadgeVariants({ level })} role="status" aria-label={`Tingkat kegawatan: ${RISK_LABEL[level]}`}>
      {RISK_LABEL[level]}
    </span>
  );
}
