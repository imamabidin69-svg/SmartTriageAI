import { cva, type VariantProps } from "class-variance-authority";
import type { HTMLAttributes } from "react";

export const cardVariants = cva("rounded-xl border bg-white dark:bg-slate-800 shadow-sm", {
  variants: {
    emphasis: {
      default: "border-slate-200 dark:border-slate-700",
      critical: "border-red-200 dark:border-red-900/60 ring-1 ring-red-100 dark:ring-red-950/40",
    },
    // Efek angkat hanya untuk kartu yang seluruh permukaannya bisa diklik (pakai tautan "stretched").
    interactive: {
      true: "relative transition-[box-shadow,translate] duration-150 hover:shadow-md motion-safe:hover:-translate-y-0.5 focus-within:ring-2 focus-within:ring-blue-500",
      false: "",
    },
    padding: {
      default: "p-5",
      compact: "p-3",
      none: "p-0",
    },
  },
  defaultVariants: { emphasis: "default", interactive: false, padding: "default" },
});

export interface CardProps extends HTMLAttributes<HTMLDivElement>, VariantProps<typeof cardVariants> {}

export function Card({ className, emphasis, interactive, padding, ...props }: CardProps) {
  return <div className={`${cardVariants({ emphasis, interactive, padding })} ${className ?? ""}`} {...props} />;
}

/** Kelas untuk tautan di dalam Card interactive agar seluruh kartu menjadi area klik. */
export const stretchedLinkClass = "after:absolute after:inset-0 after:content-[''] focus-visible:outline-none";
