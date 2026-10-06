"use client";

import "./globals.css";
import { useEffect } from "react";
import { inter } from "./fonts";

// Cadangan terakhir bila root layout sendiri gagal dirender; menggantikan seluruh dokumen.
export default function GlobalError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error("Kesalahan global:", error);
  }, [error]);

  return (
    <html lang="id" className={inter.variable}>
      <body className="min-h-dvh flex items-center justify-center px-4 bg-slate-50 text-slate-900 font-sans">
        <main className="w-full max-w-md text-center">
          <h1 className="text-xl font-bold mb-2">SmartTriage AI tidak dapat dimuat</h1>
          <p className="text-sm text-slate-600 mb-6">Terjadi kesalahan pada aplikasi. Silakan coba muat ulang.</p>
          <button
            type="button"
            onClick={reset}
            className="inline-flex h-10 items-center justify-center rounded-lg bg-blue-600 px-4 text-sm font-medium text-white hover:bg-blue-700"
          >
            Coba Muat Ulang
          </button>
        </main>
      </body>
    </html>
  );
}
