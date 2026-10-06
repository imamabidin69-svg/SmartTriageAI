"use client";

import { Moon, Sun } from "@phosphor-icons/react";
import { useUIStore } from "@/lib/store/useUIStore";

/**
 * Tombol tema. Ikon dan label dipilih lewat CSS (varian dark:) supaya tidak ada
 * selisih hidrasi antara HTML server dan tema yang dipasang skrip di <head>.
 */
export function ThemeToggleButton({ className, showLabel = false }: { className: string; showLabel?: boolean }) {
  const toggleTheme = useUIStore((s) => s.toggleTheme);

  return (
    <button type="button" onClick={toggleTheme} title="Ganti tema" className={className}>
      <Moon size={20} aria-hidden="true" className="shrink-0 dark:hidden" />
      <Sun size={20} aria-hidden="true" className="hidden shrink-0 dark:block" />
      <span className={showLabel ? "dark:hidden" : "sr-only dark:hidden"}>Aktifkan mode gelap</span>
      <span className={showLabel ? "hidden dark:inline" : "sr-only hidden dark:inline"}>Aktifkan mode terang</span>
    </button>
  );
}
