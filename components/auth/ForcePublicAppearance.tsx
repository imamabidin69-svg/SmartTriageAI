"use client";

import { useEffect } from "react";

/**
 * ForcePublicAppearance - "use client": halaman publik (login, lupa
 * password) sengaja TIDAK punya mode gelap/terang sama sekali — satu
 * tampilan tetap untuk semua orang, karena halaman ini dilihat SEBELUM ada
 * sesi (tidak ada tombol toggle tema di sini). Efek ini membersihkan sisa
 * class "dark" yang mungkin masih menempel di <html> dari halaman
 * terproteksi sebelumnya (navigasi client-side seperti router.push() tidak
 * mereset DOM <html>, hanya konten body).
 */
export function ForcePublicAppearance() {
  useEffect(() => {
    document.documentElement.classList.remove("dark");
  }, []);
  return null;
}
