import { CheckCircle, Info, Warning, WarningCircle } from "@phosphor-icons/react";
import { cva, type VariantProps } from "class-variance-authority";
import type { ReactNode } from "react";

// Kotak pesan putih dengan garis tepi kiri berwarna, sama dengan KotakPesan di aplikasi mobile.
const varian = cva("flex gap-2.5 border border-l-4 border-garis bg-white py-3 pr-4 pl-3 text-sm text-teks", {
  variants: {
    jenis: {
      info: "border-l-biru",
      galat: "border-l-kritis",
      sukses: "border-l-navy",
      peringatan: "border-l-waspada-garis",
    },
  },
  defaultVariants: { jenis: "info" },
});

const IKON = {
  info: <Info size={20} className="shrink-0 text-biru" aria-hidden />,
  galat: <WarningCircle size={20} className="shrink-0 text-galat" aria-hidden />,
  sukses: <CheckCircle size={20} className="shrink-0 text-navy" aria-hidden />,
  peringatan: <Warning size={20} className="shrink-0 text-waspada" aria-hidden />,
};

const WARNA_JUDUL = { info: "text-biru", galat: "text-galat", sukses: "text-navy", peringatan: "text-waspada" };

export interface AlertProps extends VariantProps<typeof varian> {
  judul?: string;
  children?: ReactNode;
}

export function Alert({ jenis, judul, children }: AlertProps) {
  const j = jenis ?? "info";
  // Galat dibacakan segera oleh pembaca layar; jenis lain cukup sopan.
  return (
    <div className={varian({ jenis })} role={j === "galat" ? "alert" : "status"}>
      {IKON[j]}
      <div className="min-w-0 flex-1 leading-relaxed">
        {judul ? <p className={`font-bold ${WARNA_JUDUL[j]}`}>{judul}</p> : null}
        {children ? <div className={judul ? "mt-0.5" : undefined}>{children}</div> : null}
      </div>
    </div>
  );
}
