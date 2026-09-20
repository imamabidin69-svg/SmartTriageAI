import { cva, type VariantProps } from "class-variance-authority";
import type { HTMLAttributes } from "react";

export const cardVariants = cva("rounded-xl border bg-white dark:bg-slate-800 shadow-sm transition-shadow", {
  variants: {
    emphasis: {
      default: "border-slate-200 dark:border-slate-700",
      critical: "border-red-200 dark:border-red-900/60 ring-1 ring-red-100 dark:ring-red-950/40",
      hoverable: "border-slate-200 dark:border-slate-700 hover:shadow-md hover:-translate-y-0.5",
    },
    padding: {
      default: "p-5",
      compact: "p-3",
      none: "p-0",
    },
  },
  defaultVariants: { emphasis: "default", padding: "default" },
});

export interface CardProps extends HTMLAttributes<HTMLDivElement>, VariantProps<typeof cardVariants> {}

export function Card({ className, emphasis, padding, ...props }: CardProps) {
  return <div className={`${cardVariants({ emphasis, padding })} ${className ?? ""}`} {...props} />;
}
