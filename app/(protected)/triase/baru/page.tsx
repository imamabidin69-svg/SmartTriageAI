import type { Metadata } from "next";
import { TriaseFormClient } from "@/components/triase/TriaseFormClient";
import { getSession } from "@/lib/session";

export const metadata: Metadata = {
  title: "Input Triase Baru",
  description: "Input gejala, keluhan, dan tanda vital pasien untuk diproses sistem klasifikasi AI.",
};

/**
 * app/(protected)/triase/baru/page.tsx - Server Component. Struktur halaman
 * (heading, deskripsi) dirender di server; hanya form interaktifnya
 * (TriaseFormClient) yang dibatasi "use client".
 *
 * Guard peran: sesuai tabel aktor SRS, hanya Perawat yang berwenang
 * "Input gejala & tanda vital" — DPJ TIDAK berwenang di fungsi ini
 * (wewenangnya ada di validasi/koreksi hasil, bukan input awal). Ini
 * pertahanan lapis kedua di sisi tampilan; penegakan sesungguhnya tetap di
 * Route Handler app/api/triase/route.ts (POST), karena guard di halaman
 * bisa saja terlewat kalau seseorang memanggil API langsung.
 */
export default async function TriaseBaruPage() {
  const session = await getSession(); // dijamin non-null oleh (protected)/layout.tsx

  if (session?.role !== "perawat") {
    return (
      <div
        className="max-w-3xl rounded-lg border border-amber-300 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/30 p-6"
        role="alert"
      >
        <h1 className="text-lg font-bold text-amber-900 dark:text-amber-300 mb-2">Akses Tidak Diizinkan</h1>
        <p className="text-sm text-amber-800 dark:text-amber-200">
          Hanya Perawat yang berwenang menginput gejala &amp; tanda vital pasien baru. Peran Anda saat ini tidak
          memiliki akses ke halaman ini.
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-3xl">
      <h1 className="text-xl font-bold text-slate-900 dark:text-slate-200 mb-1">Form Input Triase</h1>
      <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">
        Input gejala, keluhan, riwayat singkat, dan tanda vital pasien. Data akan diproses sistem AI untuk menghasilkan
        tingkat kegawatan beserta penjelasannya.
      </p>
      <TriaseFormClient />
    </div>
  );
}
