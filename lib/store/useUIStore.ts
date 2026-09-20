"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { RiskLevel } from "@/lib/schemas/triase.schema";

export type RiskFilter = "semua" | RiskLevel;

interface UIState {
  isSidebarOpen: boolean;
  selectedRiskFilter: RiskFilter;
  themeMode: "light" | "dark";
  toggleSidebar: () => void;
  setSelectedRiskFilter: (filter: RiskFilter) => void;
  toggleTheme: () => void;
}

/**
 * useUIStore - Client UI State murni (Modul 7, Bab B). HANYA menyimpan
 * status antarmuka lokal (sidebar, filter yang dipilih pengguna, tema).
 * Data hasil triase (Server State) TIDAK PERNAH disimpan di sini — itu
 * sepenuhnya tanggung jawab TanStack Query (lihat hooks/useTriaseQueries.ts).
 * Tidak ada <Provider> pembungkus; store bisa dipanggil langsung dari
 * Client Component manapun dengan selector presisi.
 *
 * `themeMode` dipersist ke localStorage lewat middleware `persist` Zustand
 * (`partialize` membatasi HANYA field ini yang disimpan — sidebar & filter
 * tetap murni ephemeral/sekali pakai per sesi tab, sesuai dokumentasi
 * Matriks Modul 7). Ini memperbaiki bug: sebelumnya tema hanya hidup di
 * memori JS, sehingga navigasi yang memicu reload penuh (atau refresh
 * browser) selalu mengembalikannya ke "light" — kini tema konsisten di
 * semua rute dan bertahan lintas sesi.
 */
export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      isSidebarOpen: true,
      selectedRiskFilter: "semua",
      themeMode: "light",
      toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
      setSelectedRiskFilter: (filter) => set({ selectedRiskFilter: filter }),
      toggleTheme: () => set((state) => ({ themeMode: state.themeMode === "light" ? "dark" : "light" })),
    }),
    {
      name: "smarttriage-ui-preferences",
      partialize: (state) => ({ themeMode: state.themeMode }),
    },
  ),
);
