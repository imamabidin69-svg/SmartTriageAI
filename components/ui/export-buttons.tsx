"use client";

import { Button } from "@/components/ui/button";
import { buildCsv, downloadCsv } from "@/lib/csv-export";

interface ExportButtonsProps {
  filenamePrefix: string;
  headers: string[];
  rows: string[][];
}

/**
 * ExportButtons - "use client": satu-satunya bagian interaktif di halaman
 * laporan (Server Component). Menerima data yang SUDAH di-fetch di server
 * sebagai props biasa (headers/rows string) — tidak perlu fetch ulang di
 * klien, jadi tetap konsisten dengan prinsip RSC-dominan (Modul 6).
 *
 * "Cetak / Simpan sebagai PDF" memakai window.print() bawaan browser (lihat
 * @media print di globals.css) alih-alih pustaka PDF eksternal yang berat —
 * pengguna tinggal pilih "Simpan sebagai PDF" di dialog cetak browser.
 */
export function ExportButtons({ filenamePrefix, headers, rows }: ExportButtonsProps) {
  function handleExportCsv() {
    const csv = buildCsv(headers, rows);
    const tanggal = new Date().toISOString().slice(0, 10);
    downloadCsv(`${filenamePrefix}-${tanggal}.csv`, csv);
  }

  function handlePrint() {
    // Kelas dark: Tailwind bergantung pada class ".dark" di <html>, bukan
    // media type — jadi override CSS saja tidak cukup untuk memaksa mode
    // terang saat dialog cetak muncul. Lepas sementara class "dark", cetak,
    // lalu kembalikan sesuai preferensi tema pengguna sebelumnya.
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
