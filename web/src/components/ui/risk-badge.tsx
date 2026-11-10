import type { RiskLevel } from "@/api/tipe";
import { LABEL_LEVEL } from "@/lib/label";

// Hanya Kritis yang berlatar merah penuh. Level lain cukup kotak kecil berwarna dan teks tebal, jadi level
// tetap terbaca tanpa mengandalkan warna (sama dengan aplikasi mobile).
const WARNA_KOTAK: Record<RiskLevel, string> = {
  kritis: "bg-white",
  tinggi: "bg-tinggi",
  sedang: "bg-sedang",
  rendah: "bg-rendah",
};

export function RiskBadge({ level }: { level: RiskLevel }) {
  const kritis = level === "kritis";
  return (
    <span
      className={`inline-flex items-center gap-1.5 text-sm font-bold ${
        kritis ? "rounded bg-kritis px-2 py-0.5 text-white" : "text-teks"
      }`}
    >
      <span aria-hidden className={`rounded-[2px] ${kritis ? "size-1.5" : "size-2.5"} ${WARNA_KOTAK[level]}`} />
      {LABEL_LEVEL[level]}
    </span>
  );
}
