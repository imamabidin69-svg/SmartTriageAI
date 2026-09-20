"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Role } from "@/lib/schemas/triase.schema";
import { useUIStore } from "@/lib/store/useUIStore";

const NAV_ITEMS: Array<{ href: string; label: string; roles?: Role[] }> = [
  { href: "/dashboard", label: "Dashboard Antrean", roles: ["perawat", "dokter_pj"] },
  { href: "/triase/baru", label: "Input Triase", roles: ["perawat"] },
  { href: "/pasien", label: "Registrasi Pasien", roles: ["petugas_pendaftaran", "perawat"] },
  { href: "/riwayat-pasien", label: "Riwayat Triase", roles: ["perawat", "dokter_pj"] },
  { href: "/asesmen-visual", label: "Asesmen Pasien Tidak Sadar", roles: ["perawat"] },
  { href: "/admin/staff", label: "Kelola Akun Staf", roles: ["admin_faskes"] },
  { href: "/admin/laporan", label: "Laporan & Statistik", roles: ["admin_faskes"] },
  { href: "/superadmin", label: "Kelola Faskes", roles: ["super_admin"] },
  { href: "/superadmin/konfigurasi-ai", label: "Konfigurasi Model AI", roles: ["super_admin"] },
  { href: "/auditor", label: "Log Audit", roles: ["auditor"] },
  { href: "/dinas-kesehatan", label: "Laporan Regional", roles: ["dinas_kesehatan"] },
];

export function DashboardSidebarNavClient({ role }: { role: Role }) {
  const isSidebarOpen = useUIStore((s) => s.isSidebarOpen);
  const pathname = usePathname();

  if (!isSidebarOpen) return null;

  const visibleItems = NAV_ITEMS.filter((item) => !item.roles || item.roles.includes(role));

  return (
    <nav
      id="dashboard-sidebar"
      aria-label="Navigasi Utama"
      className="w-64 shrink-0 bg-white dark:bg-slate-800 p-5 border-r border-slate-200 dark:border-slate-700 h-fit md:sticky md:top-[89px] print:hidden"
    >
      <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">Navigasi</h2>
      <ul className="flex flex-col gap-2">
        {visibleItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <li key={item.href}>
              <Link
                href={item.href}
                aria-current={isActive ? "page" : undefined}
                className={
                  isActive
                    ? "block px-3 py-2 text-sm font-medium rounded-lg bg-blue-50 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300"
                    : "block px-3 py-2 text-sm font-medium rounded-lg text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
                }
              >
                {item.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
