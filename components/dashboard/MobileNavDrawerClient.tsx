"use client";

import { SignOut, X } from "@phosphor-icons/react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef } from "react";
import { ThemeToggleButton } from "@/components/dashboard/ThemeToggleButton";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import { navItemsForRole, navLinkClass } from "@/lib/nav-items";
import type { Role } from "@/lib/schemas/triase.schema";
import { useUIStore } from "@/lib/store/useUIStore";

export const MOBILE_NAV_ID = "dashboard-sidebar-drawer";

const panelButtonClass =
  "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-700";

interface MobileNavDrawerProps {
  role: Role;
  nama: string;
  roleLabel: string;
  onLogout: () => void;
}

/**
 * Drawer navigasi untuk layar di bawah 768px. Memakai <dialog> modal:
 * top layer, fokus terkunci, Esc bawaan, dan latar belakang otomatis inert.
 */
export function MobileNavDrawerClient({ role, nama, roleLabel, onLogout }: MobileNavDrawerProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const isOpen = useUIStore((s) => s.isMobileNavOpen);
  const setOpen = useUIStore((s) => s.setMobileNavOpen);
  const isDesktop = useMediaQuery("(min-width: 768px)");
  const pathname = usePathname();

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (isOpen && !dialog.open) dialog.showModal();
    if (!isOpen && dialog.open) dialog.close();
  }, [isOpen]);

  // Light dismiss: closedby="any" bila didukung browser, selain itu cek klik di luar panel.
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if ("closedBy" in HTMLDialogElement.prototype) {
      dialog.setAttribute("closedby", "any");
      return;
    }
    function handleBackdropClick(event: MouseEvent) {
      if (!dialog || event.target !== dialog) return;
      const rect = dialog.getBoundingClientRect();
      const diDalamPanel =
        rect.top <= event.clientY &&
        event.clientY <= rect.bottom &&
        rect.left <= event.clientX &&
        event.clientX <= rect.right;
      if (!diDalamPanel) dialog.close();
    }
    dialog.addEventListener("click", handleBackdropClick);
    return () => dialog.removeEventListener("click", handleBackdropClick);
  }, []);

  // Drawer tidak relevan di layar lebar; tutup kalau jendela melebar saat drawer terbuka.
  useEffect(() => {
    if (isDesktop) setOpen(false);
  }, [isDesktop, setOpen]);

  const tutup = () => setOpen(false);

  return (
    <dialog
      ref={dialogRef}
      id={MOBILE_NAV_ID}
      aria-label="Navigasi Utama"
      onClose={tutup}
      className="nav-drawer bg-white text-slate-900 shadow-xl dark:bg-slate-800 dark:text-slate-100"
    >
      <div className="flex h-full flex-col">
        <div className="flex h-(--header-h) shrink-0 items-center justify-between gap-3 border-b border-slate-200 px-4 dark:border-slate-700">
          <Link href="/profil" onClick={tutup} className="min-w-0 rounded-lg hover:underline">
            <span className="block truncate text-sm font-semibold">{nama}</span>
            <span className="block truncate text-xs text-slate-500 dark:text-slate-400">{roleLabel}</span>
          </Link>
          <button
            type="button"
            onClick={tutup}
            aria-label="Tutup navigasi"
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-700"
          >
            <X size={20} aria-hidden="true" />
          </button>
        </div>

        <nav aria-label="Navigasi Utama" className="flex-1 overflow-y-auto p-4">
          <ul className="flex flex-col gap-2">
            {navItemsForRole(role).map((item) => {
              const isActive = pathname === item.href;
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    onClick={tutup}
                    aria-current={isActive ? "page" : undefined}
                    className={navLinkClass(isActive)}
                  >
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        <div className="shrink-0 space-y-1 border-t border-slate-200 p-4 dark:border-slate-700">
          <ThemeToggleButton className={panelButtonClass} showLabel />
          <button
            type="button"
            onClick={() => {
              tutup();
              onLogout();
            }}
            className={panelButtonClass}
          >
            <SignOut size={20} aria-hidden="true" className="shrink-0" />
            Keluar
          </button>
        </div>
      </div>
    </dialog>
  );
}
