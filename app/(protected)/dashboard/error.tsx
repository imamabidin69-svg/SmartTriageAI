"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";

export default function DashboardError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error("Dashboard error:", error);
  }, [error]);

  return (
    <div
      className="rounded-lg border border-red-200 bg-red-50 dark:bg-red-950/30 dark:border-red-900 p-6 text-center"
      role="alert"
    >
      <p className="text-red-800 dark:text-red-300 font-medium mb-3">
        Terjadi kesalahan saat memuat dashboard antrean.
      </p>
      <Button type="button" variant="destructive" onClick={reset}>
        Coba Muat Ulang
      </Button>
    </div>
  );
}
