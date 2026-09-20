"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { usePendingPasswordResetsQuery } from "@/hooks/useStaffQueries";
import { useKritisWatchQuery } from "@/hooks/useTriaseQueries";
import type { Session } from "@/lib/schemas/triase.schema";
import { useUIStore } from "@/lib/store/useUIStore";

const ROLE_LABEL: Record<Session["role"], string> = {
  perawat: "Perawat",
  dokter_pj: "Dokter Penanggung Jawab (DPJ)",
  petugas_pendaftaran: "Petugas Pendaftaran",
  admin_faskes: "Admin Fasilitas Kesehatan",
  super_admin: "Super Admin",
  auditor: "Auditor",
  dinas_kesehatan: "Dinas Kesehatan",
};

export function DashboardHeaderClient({ session }: { session: Session }) {
  const isSidebarOpen = useUIStore((s) => s.isSidebarOpen);
  const themeMode = useUIStore((s) => s.themeMode);
  const toggleSidebar = useUIStore((s) => s.toggleSidebar);
  const toggleTheme = useUIStore((s) => s.toggleTheme);
  const router = useRouter();
  const isAdmin = session.role === "admin_faskes";
  const isDpj = session.role === "dokter_pj";
  const { data: pendingResets } = usePendingPasswordResetsQuery(isAdmin);
  const pendingCount = pendingResets?.length ?? 0;
  const { data: kritisPending } = useKritisWatchQuery(isDpj);
  const kritisCount = kritisPending?.length ?? 0;

  useEffect(() => {
    document.documentElement.classList.toggle("dark", themeMode === "dark");
  }, [themeMode]);

  async function handleLogout() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/login");
    router.refresh();
  }

  return (
    <header className="bg-slate-800 text-white shadow-sm sticky top-0 z-10 border-b border-slate-700/50 print:hidden">
      <div className="max-w-6xl mx-auto px-4 py-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={toggleSidebar}
            aria-expanded={isSidebarOpen}
            aria-controls="dashboard-sidebar"
            className="w-9 h-9 flex items-center justify-center rounded-md bg-slate-700 hover:bg-slate-600 text-white"
            aria-label={isSidebarOpen ? "Sembunyikan navigasi" : "Tampilkan navigasi"}
          >
            ☰
          </button>
          <div
            className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center font-bold text-lg"
            aria-hidden="true"
          >
            ST
          </div>
          <div>
            <h1 className="text-lg font-bold leading-tight">SmartTriage AI</h1>
            <p className="text-xs text-slate-400">Sistem Bantu Triase &mdash; IGD &amp; Puskesmas</p>
          </div>
        </div>

        <div className="flex items-center gap-3 text-sm">
          {isDpj && (
            <Link
              href="/dashboard"
              className="relative w-9 h-9 flex items-center justify-center rounded-md bg-slate-700 hover:bg-slate-600"
              aria-label={
                kritisCount > 0 ? `${kritisCount} kasus kritis menunggu validasi` : "Tidak ada kasus kritis menunggu"
              }
              title="Kasus kritis menunggu validasi"
            >
              🚨
              {kritisCount > 0 && (
                <span
                  className="absolute -top-1 -right-1 min-w-[18px] h-[18px] px-1 flex items-center justify-center rounded-full bg-red-600 text-white text-[10px] font-bold"
                  aria-hidden="true"
                >
                  {kritisCount}
                </span>
              )}
            </Link>
          )}
          {isAdmin && (
            <Link
              href="/admin/staff"
              className="relative w-9 h-9 flex items-center justify-center rounded-md bg-slate-700 hover:bg-slate-600"
              aria-label={
                pendingCount > 0
                  ? `${pendingCount} permintaan reset password menunggu`
                  : "Tidak ada permintaan reset password menunggu"
              }
              title="Permintaan reset password"
            >
              🔔
              {pendingCount > 0 && (
                <span
                  className="absolute -top-1 -right-1 min-w-[18px] h-[18px] px-1 flex items-center justify-center rounded-full bg-red-600 text-white text-[10px] font-bold"
                  aria-hidden="true"
                >
                  {pendingCount}
                </span>
              )}
            </Link>
          )}
          <button
            type="button"
            onClick={toggleTheme}
            className="w-9 h-9 flex items-center justify-center rounded-md bg-slate-700 hover:bg-slate-600"
            aria-label={themeMode === "light" ? "Aktifkan mode gelap" : "Aktifkan mode terang"}
            title="Tema (Client UI State — Zustand)"
          >
            {themeMode === "light" ? "🌙" : "☀️"}
          </button>
          <Link href="/profil" className="text-slate-300 hover:text-white hover:underline">
            {session.nama}
          </Link>
          <span className="text-slate-400 hidden sm:inline">&middot; {ROLE_LABEL[session.role]}</span>
          <Button type="button" variant="outline" size="sm" onClick={() => void handleLogout()}>
            Keluar
          </Button>
        </div>
      </div>
    </header>
  );
}
