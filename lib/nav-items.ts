import type { Role } from "@/lib/schemas/triase.schema";

export interface NavItem {
  href: string;
  label: string;
  roles?: Role[];
}

/** Label dan tujuan navigasi utama. Dipakai sidebar desktop dan drawer mobile. */
export const NAV_ITEMS: NavItem[] = [
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

export function navItemsForRole(role: Role): NavItem[] {
  return NAV_ITEMS.filter((item) => !item.roles || item.roles.includes(role));
}

export function navLinkClass(isActive: boolean): string {
  return isActive
    ? "block px-3 py-2 text-sm font-medium rounded-lg bg-blue-50 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300"
    : "block px-3 py-2 text-sm font-medium rounded-lg text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700";
}
