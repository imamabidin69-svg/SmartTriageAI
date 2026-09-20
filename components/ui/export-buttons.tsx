"use client";

import { Button } from "@/components/ui/button";
import { buildCsv, downloadCsv } from "@/lib/csv-export";

interface ExportButtonsProps {
  filenamePrefix: string;
  headers: string[];
  rows: string[][];
}

export function ExportButtons({ filenamePrefix, headers, rows }: ExportButtonsProps) {
  function handleExportCsv() {
    const csv = buildCsv(headers, rows);
    const tanggal = new Date().toISOString().slice(0, 10);
    downloadCsv(`${filenamePrefix}-${tanggal}.csv`, csv);
  }

  function handlePrint() {
    const isDark = document.documentElement.classList.contains("dark");
    if (isDark) document.documentElement.classList.remove("dark");
    window.print();
    if (isDark) document.documentElement.classList.add("dark");
  }

  return (
    <div className="flex gap-2 print:hidden">
      <Button type="button" variant="outline" size="sm" onClick={handleExportCsv}>
        ⬇ Unduh CSV
      </Button>
      <Button type="button" variant="outline" size="sm" onClick={handlePrint}>
        🖨 Cetak / Simpan PDF
      </Button>
    </div>
  );
}
