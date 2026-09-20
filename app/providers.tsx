"use client";

import { QueryClientProvider } from "@tanstack/react-query";
import { type ReactNode, useState } from "react";
import { getBrowserQueryClient } from "@/lib/query-client";

/**
 * Providers - satu-satunya alasan file ini "use client": QueryClientProvider
 * menyimpan instance QueryClient di dalam React Context, dan Context Provider
 * WAJIB berupa Client Component (Modul 6, Bab C). RootLayout di app/layout.tsx
 * sendiri TETAP Server Component; hanya potongan kecil ini yang dibatasi
 * "use client" (prinsip Leaf Components / Component Boundary, Modul 6).
 */
export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(() => getBrowserQueryClient());
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
