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
