"use client";

import { QueryClientProvider } from "@tanstack/react-query";
import { type ReactNode, useState } from "react";
import { getBrowserQueryClient } from "@/lib/query-client";

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(() => getBrowserQueryClient());
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
