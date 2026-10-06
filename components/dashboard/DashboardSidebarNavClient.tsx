"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { navItemsForRole, navLinkClass } from "@/lib/nav-items";
import type { Role } from "@/lib/schemas/triase.schema";
import { useUIStore } from "@/lib/store/useUIStore";

/** Navigasi utama untuk layar md ke atas. Di layar kecil navigasi pindah ke drawer. */
export function DashboardSidebarNavClient({ role }: { role: Role }) {
  const isSidebarOpen = useUIStore((s) => s.isSidebarOpen);
  const pathname = usePathname();

  if (!isSidebarOpen) return null;

  return (
    <nav
      id="dashboard-sidebar"
      aria-label="Navigasi Utama"
      className="hidden w-68 shrink-0 bg-white dark:bg-slate-800 p-5 border-r border-slate-200 dark:border-slate-700 h-fit md:block md:sticky md:top-[calc(var(--header-h)+1rem)] print:hidden"
    >
      <ul className="flex flex-col gap-2">
        {navItemsForRole(role).map((item) => {
          const isActive = pathname === item.href;
          return (
            <li key={item.href}>
              <Link href={item.href} aria-current={isActive ? "page" : undefined} className={navLinkClass(isActive)}>
                {item.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
