/// <reference types="vitest/config" />
import path from "node:path";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import { VitePWA } from "vite-plugin-pwa";

// Saat development, request /api diteruskan ke Flask supaya cookie login berada di origin yang sama.
const ALAMAT_BACKEND = process.env.ALAMAT_BACKEND ?? "http://127.0.0.1:5000";

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: "autoUpdate",
      // registerSW.js berupa berkas terpisah, bukan skrip inline, supaya lolos CSP script-src 'self'.
      injectRegister: "script",
      includeAssets: ["apple-touch-icon.png"],
      manifest: {
        name: "SmartTriage AI Admin",
        short_name: "SmartTriage",
        description: "Web admin IGD SmartTriage AI: kelola staf, pengaturan triase, rekap, dan log audit.",
        lang: "id",
        start_url: "/staf",
        scope: "/",
        display: "standalone",
        background_color: "#f8fafc",
        theme_color: "#1e293b",
        icons: [
          { src: "/ikon-192.png", sizes: "192x192", type: "image/png" },
          { src: "/ikon-512.png", sizes: "512x512", type: "image/png" },
          { src: "/ikon-maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
        ],
      },
      workbox: {
        // Hanya aset build yang disimpan. Respons API berisi data pasien dan tidak pernah di-cache.
        globPatterns: ["**/*.{js,css,html,woff2,png,svg}"],
        navigateFallback: "/index.html",
        navigateFallbackDenylist: [/^\/api\//],
        runtimeCaching: [],
      },
    }),
  ],
  resolve: {
    alias: { "@": path.resolve(import.meta.dirname, "src") },
  },
  server: {
    proxy: { "/api": { target: ALAMAT_BACKEND, changeOrigin: false } },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/uji/setup.ts"],
    include: ["src/**/*.test.{ts,tsx}"],
    restoreMocks: true,
    unstubGlobals: true,
    coverage: {
      provider: "v8",
      reporter: ["text", "lcov"],
      reportsDirectory: "./coverage",
      include: ["src/**/*.{ts,tsx}"],
      exclude: ["src/**/*.test.{ts,tsx}", "src/uji/**", "src/main.tsx", "src/api/skema.d.ts", "src/vite-env.d.ts"],
      thresholds: { lines: 80, functions: 80, branches: 80, statements: 80 },
    },
  },
});
