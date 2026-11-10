import { cva, type VariantProps } from "class-variance-authority";
import type { ButtonHTMLAttributes } from "react";

// Tombol mengikuti panduan gaya tahap 6D: sudut 6px, datar tanpa bayangan, fokus jelas dengan cincin biru.
// Varian ghost dipakai untuk aksi di tabel sehingga terbaca seperti tautan.
export const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-md text-[15px] font-bold whitespace-nowrap " +
    "transition-colors duration-150 " +
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-biru " +
    "disabled:opacity-50 disabled:pointer-events-none",
  {
    variants: {
      variant: {
        default: "bg-biru text-white hover:bg-biru-tua",
        destructive: "bg-galat text-white hover:bg-[#9a1e14]",
        outline: "border border-biru-garis bg-white text-biru hover:bg-biru-muda",
        ghost: "text-biru hover:bg-biru-muda",
      },
      size: {
        default: "h-10 px-4",
        sm: "h-9 px-3 text-sm",
        lg: "h-12 px-6 text-base",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  },
);

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {}

export function Button({ className, variant, size, type = "button", ...props }: ButtonProps) {
  return <button type={type} className={`${buttonVariants({ variant, size })} ${className ?? ""}`} {...props} />;
}
