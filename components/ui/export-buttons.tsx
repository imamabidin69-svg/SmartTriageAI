"use client";

import { DownloadSimple, Printer } from "@phosphor-icons/react";
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
        <DownloadSimple size={16} aria-hidden="true" />
        Unduh CSV
      </Button>
      <Button type="button" variant="outline" size="sm" onClick={handlePrint}>
        <Printer size={16} aria-hidden="true" />
        Cetak / Simpan PDF
      </Button>
    </div>
  );
}
