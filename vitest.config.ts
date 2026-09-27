import path from "node:path";
import { defineConfig } from "vitest/config";

export default defineConfig({
  resolve: {
    alias: {
      // Paket "server-only" sengaja throw error kalau di-resolve lewat kondisi
      // "default" (di luar runtime React Server Component Next.js) - lihat
      // node_modules/server-only/package.json. Vitest berjalan di Node biasa,
      // jadi dialihkan ke empty.js (no-op) bawaan paket yang sama supaya
      // lib/ml-client.ts dan modul server-only lain bisa di-import di test
      // tanpa perlu menyalin ulang isi paketnya.
      "server-only": path.resolve(__dirname, "node_modules/server-only/empty.js"),
      "@": __dirname,
    },
  },
  test: {
    environment: "node",
    include: ["**/*.test.ts"],
    exclude: ["node_modules/**", ".next/**"],
    coverage: {
      provider: "v8",
      reporter: ["text", "lcov"],
      reportsDirectory: "./coverage",
      // Fokus ke kode yang punya logika (lib/), bukan skema Zod deklaratif
      // atau seed data statis - keduanya tidak banyak berarti diberi "test"
      // tersendiri dan bukan sumber bug yang realistis.
      include: ["lib/**/*.ts"],
      exclude: ["lib/**/*.test.ts", "lib/schemas/**", "lib/data/**", "lib/types/**"],
    },
  },
});
