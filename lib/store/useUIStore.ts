"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { UI_PREFERENCES_KEY } from "@/lib/constants";
import type { RiskLevel } from "@/lib/schemas/triase.schema";

export type RiskFilter = "semua" | RiskLevel;

/** "system" mengikuti preferensi OS; "light" dan "dark" berarti dikunci pengguna lewat tombol tema. */
export type ThemeMode = "system" | "light" | "dark";

interface UIState {
  isSidebarOpen: boolean;
  isMobileNavOpen: boolean;
  selectedRiskFilter: RiskFilter;
  themeMode: ThemeMode;
  toggleSidebar: () => void;
  setMobileNavOpen: (open: boolean) => void;
  setSelectedRiskFilter: (filter: RiskFilter) => void;
  toggleTheme: () => void;
}

export function resolveTheme(mode: ThemeMode, systemPrefersDark: boolean): "light" | "dark" {
  if (mode === "system") return systemPrefersDark ? "dark" : "light";
  return mode;
}

function systemPrefersDark(): boolean {
  return typeof window !== "undefined" && window.matchMedia("(prefers-color-scheme: dark)").matches;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      isSidebarOpen: true,
      isMobileNavOpen: false,
      selectedRiskFilter: "semua",
      themeMode: "system",
      toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
      setMobileNavOpen: (open) => set({ isMobileNavOpen: open }),
      setSelectedRiskFilter: (filter) => set({ selectedRiskFilter: filter }),
      // Dua keadaan: ikut sistem, atau dikunci ke kebalikannya. Setiap klik pasti mengubah tampilan.
      toggleTheme: () =>
        set((state) => {
          const sistemGelap = systemPrefersDark();
          const berikutnya = resolveTheme(state.themeMode, sistemGelap) === "dark" ? "light" : "dark";
          const temaSistem = sistemGelap ? "dark" : "light";
          return { themeMode: berikutnya === temaSistem ? "system" : berikutnya };
        }),
    }),
    {
      name: UI_PREFERENCES_KEY,
      partialize: (state) => ({ themeMode: state.themeMode }),
    },
  ),
);
