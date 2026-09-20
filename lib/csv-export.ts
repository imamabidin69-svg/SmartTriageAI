"use client";

/** Escape nilai sel CSV sesuai RFC 4180 (bungkus tanda kutip jika mengandung koma/kutip/baris baru). */
function escapeCsvCell(value: string): string {
  if (/[",\n]/.test(value)) {
    return `"${value.replace(/"/g, '""')}"`;
  }
  return value;
}

/** Bangun string CSV dari array header + array baris (array of array of string). */
export function buildCsv(headers: string[], rows: string[][]): string {
  const lines = [headers, ...rows].map((row) => row.map(escapeCsvCell).join(","));
  // \uFEFF (BOM) di depan supaya Excel mendeteksi UTF-8 dengan benar (mis. karakter °, ₂, dst tidak jadi karakter aneh).
  return `\uFEFF${lines.join("\r\n")}`;
}

/** Picu unduhan file CSV di browser lewat Blob + elemen <a> sementara. */
export function downloadCsv(filename: string, csvContent: string): void {
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
