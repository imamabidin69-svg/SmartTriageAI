import { defaultShouldDehydrateQuery, QueryClient } from "@tanstack/react-query";
import { cache } from "react";

/**
 * makeQueryClient - konfigurasi default staleTime/gcTime (Modul 7, Bab C).
 * Dipanggil baik di server (prefetch untuk SSR) maupun browser (Provider).
 */
function makeQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 1000 * 60, // 1 menit - data antrean berubah cukup sering (kegawatan pasien)
        gcTime: 1000 * 60 * 15, // 15 menit
      },
      dehydrate: {
        // Sertakan juga query yang masih "pending" saat dehydrate, agar
        // Suspense/streaming dari Server Component tetap konsisten.
        shouldDehydrateQuery: (query) => defaultShouldDehydrateQuery(query) || query.state.status === "pending",
      },
    },
  });
}

let browserQueryClient: QueryClient | undefined;

/**
 * getQueryClient() - di SERVER: satu instance baru per request (dibungkus
 * React cache() supaya beberapa Server Component dalam satu request berbagi
 * instance yang sama tanpa kebocoran data antar-pengguna). Di BROWSER: satu
 * singleton yang bertahan sepanjang sesi tab agar cache tidak hilang saat
 * navigasi client-side.
 */
export const getQueryClient = cache(makeQueryClient);

export function getBrowserQueryClient(): QueryClient {
  if (typeof window === "undefined") {
    // Sisi server tidak boleh memakai singleton browser — selalu buat baru.
    return makeQueryClient();
  }
  if (!browserQueryClient) {
    browserQueryClient = makeQueryClient();
  }
  return browserQueryClient;
}
