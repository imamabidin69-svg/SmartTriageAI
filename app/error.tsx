"use client";

import Link from "next/link";
import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { StatusPage } from "@/components/ui/status-page";

export default function AppError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error("Kesalahan aplikasi:", error);
  }, [error]);

  return (
    <StatusPage title="Halaman gagal dimuat">
      <p className="text-sm text-slate-600 dark:text-slate-400 mb-6">
        Terjadi kesalahan saat memuat halaman ini. Coba muat ulang; kalau masih gagal, kembali ke halaman utama.
      </p>
      <div className="flex flex-wrap items-center justify-center gap-3">
        <Button type="button" onClick={reset}>
          Coba Muat Ulang
        </Button>
        <Link href="/" className="text-sm font-medium text-blue-600 dark:text-blue-400 hover:underline">
          Kembali ke halaman utama
        </Link>
      </div>
    </StatusPage>
  );
}
