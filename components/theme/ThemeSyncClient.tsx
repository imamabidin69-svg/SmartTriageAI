"use client";

import { useEffect } from "react";
import { resolveTheme, useUIStore } from "@/lib/store/useUIStore";

/**
 * Menyelaraskan kelas tema di <html> dengan pilihan pengguna dan preferensi sistem.
 * Tema awal sudah dipasang skrip di <head>; komponen ini menangani perubahan sesudahnya.
 */
export function ThemeSyncClient() {
  useEffect(() => {
    const mql = window.matchMedia("(prefers-color-scheme: dark)");

    function terapkanTema() {
      const { themeMode } = useUIStore.getState();
      const root = document.documentElement;
      root.classList.toggle("dark", resolveTheme(themeMode, mql.matches) === "dark");
      root.classList.toggle("light", themeMode === "light");
    }

    terapkanTema();
    const berhentiDengar = useUIStore.subscribe(terapkanTema);
    mql.addEventListener("change", terapkanTema);
    return () => {
      berhentiDengar();
      mql.removeEventListener("change", terapkanTema);
    };
  }, []);

  return null;
}
