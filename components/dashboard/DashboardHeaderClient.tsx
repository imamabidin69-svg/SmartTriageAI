"use client";

import { Bell, List, Siren } from "@phosphor-icons/react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { MOBILE_NAV_ID, MobileNavDrawerClient } from "@/components/dashboard/MobileNavDrawerClient";
import { ThemeToggleButton } from "@/components/dashboard/ThemeToggleButton";
import { Button } from "@/components/ui/button";
import { useMediaQuery } from "@/hooks/useMediaQuery";
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

const iconButtonClass =
  "relative flex h-9 w-9 items-center justify-center rounded-lg bg-slate-700 text-white hover:bg-slate-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400";

const countBadgeClass =
  "absolute -top-1 -right-1 min-w-[18px] h-[18px] px-1 flex items-center justify-center rounded-full bg-red-600 text-white text-[10px] font-bold tabular-nums";

export function DashboardHeaderClient({ session }: { session: Session }) {
  const isSidebarOpen = useUIStore((s) => s.isSidebarOpen);
  const isMobileNavOpen = useUIStore((s) => s.isMobileNavOpen);
  const toggleSidebar = useUIStore((s) => s.toggleSidebar);
  const setMobileNavOpen = useUIStore((s) => s.setMobileNavOpen);
  const isDesktop = useMediaQuery("(min-width: 768px)");
  const router = useRouter();
  const isAdmin = session.role === "admin_faskes";
  const isDpj = session.role === "dokter_pj";
  const { data: pendingResets } = usePendingPasswordResetsQuery(isAdmin);
  const pendingCount = pendingResets?.length ?? 0;
  const { data: kritisPending } = useKritisWatchQuery(isDpj);
  const kritisCount = kritisPending?.length ?? 0;

  const navTerbuka = isDesktop ? isSidebarOpen : isMobileNavOpen;

  async function handleLogout() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/login");
    router.refresh();
  }

  return (
    <header className="bg-slate-800 text-white shadow-sm sticky top-0 z-(--z-header) border-b border-slate-700/50 print:hidden">
      <div className="max-w-6xl mx-auto px-4 h-(--header-h) flex items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-3">
          <button
            type="button"
            onClick={() => (isDesktop ? toggleSidebar() : setMobileNavOpen(true))}
            aria-expanded={navTerbuka}
            aria-controls={isDesktop ? "dashboard-sidebar" : MOBILE_NAV_ID}
            className={iconButtonClass}
            aria-label={navTerbuka ? "Sembunyikan navigasi" : "Tampilkan navigasi"}
          >
            <List size={20} aria-hidden="true" />
          </button>
          <div
            className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center font-bold text-lg shrink-0"
            aria-hidden="true"
          >
            ST
          </div>
          <div className="min-w-0">
            <p className="text-lg font-bold leading-tight">SmartTriage AI</p>
            <p className="hidden truncate text-xs text-slate-400 sm:block">
              Sistem Bantu Triase untuk IGD &amp; Puskesmas
            </p>
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-3 text-sm">
          {isDpj && (
            <Link
              href="/dashboard"
              className={iconButtonClass}
              aria-label={
                kritisCount > 0 ? `${kritisCount} kasus kritis menunggu validasi` : "Tidak ada kasus kritis menunggu"
              }
              title="Kasus kritis menunggu validasi"
            >
              <Siren size={20} aria-hidden="true" />
              {kritisCount > 0 && (
                <span className={countBadgeClass} aria-hidden="true">
                  {kritisCount}
                </span>
              )}
            </Link>
          )}
          {isAdmin && (
            <Link
              href="/admin/staff"
              className={iconButtonClass}
              aria-label={
                pendingCount > 0
                  ? `${pendingCount} permintaan reset password menunggu`
                  : "Tidak ada permintaan reset password menunggu"
              }
              title="Permintaan reset password"
            >
              <Bell size={20} aria-hidden="true" />
              {pendingCount > 0 && (
                <span className={countBadgeClass} aria-hidden="true">
                  {pendingCount}
                </span>
              )}
            </Link>
          )}
          <div className="hidden md:block">
            <ThemeToggleButton className={iconButtonClass} />
          </div>
          <Link
            href="/profil"
            className="hidden max-w-[12rem] truncate text-slate-300 hover:text-white hover:underline md:inline-block"
          >
            {session.nama}
          </Link>
          <span className="text-slate-400 hidden lg:inline">&middot; {ROLE_LABEL[session.role]}</span>
          <div className="hidden md:block">
            <Button type="button" variant="outline" size="sm" onClick={() => void handleLogout()}>
              Keluar
            </Button>
          </div>
        </div>
      </div>

      <MobileNavDrawerClient
        role={session.role}
        nama={session.nama}
        roleLabel={ROLE_LABEL[session.role]}
        onLogout={() => void handleLogout()}
      />
    </header>
  );
}
