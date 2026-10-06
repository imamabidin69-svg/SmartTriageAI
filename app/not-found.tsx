import type { Metadata } from "next";
import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";
import { StatusPage } from "@/components/ui/status-page";

export const metadata: Metadata = {
  title: "Halaman Tidak Ditemukan",
};

export default function NotFound() {
  return (
    <StatusPage title="Halaman tidak ditemukan">
      <p className="text-sm text-slate-600 dark:text-slate-400 mb-6">
        Alamat yang Anda buka tidak ada di SmartTriage AI. Periksa lagi tautannya.
      </p>
      <Link href="/" className={buttonVariants()}>
        Kembali ke halaman utama
      </Link>
    </StatusPage>
  );
}
