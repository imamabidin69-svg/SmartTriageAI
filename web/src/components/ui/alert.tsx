import { cva, type VariantProps } from "class-variance-authority";
import type { ReactNode } from "react";

const varian = cva("rounded-lg border px-4 py-3 text-sm", {
  variants: {
    jenis: {
      info: "border-slate-200 bg-slate-50 text-slate-700",
      galat: "border-red-200 bg-red-50 text-red-800",
      sukses: "border-emerald-200 bg-emerald-50 text-emerald-800",
      peringatan: "border-amber-200 bg-amber-50 text-amber-900",
    },
  },
  defaultVariants: { jenis: "info" },
});

export interface AlertProps extends VariantProps<typeof varian> {
  judul?: string;
  children?: ReactNode;
}

export function Alert({ jenis, judul, children }: AlertProps) {
  // Galat dibacakan segera oleh pembaca layar; jenis lain cukup sopan.
  return (
    <div className={varian({ jenis })} role={jenis === "galat" ? "alert" : "status"}>
      {judul ? <p className="font-semibold">{judul}</p> : null}
      {children ? <div className={judul ? "mt-1" : undefined}>{children}</div> : null}
    </div>
  );
}
