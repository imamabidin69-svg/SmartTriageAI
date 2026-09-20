import localFont from "next/font/local";

/**
 * next/font/local (Modul 6, Bab F) - berkas font Inter di-host sendiri lewat
 * paket @fontsource/inter (diunduh sekali saat `npm install`, bukan di-fetch
 * ke Google Fonts saat build/runtime). next/font tetap menetapkan dimensi
 * CSS font secara eksplisit di build-time untuk mendukung CLS <= 0.1,
 * persis seperti next/font/google — bedanya hanya sumber berkas fontnya.
 */
export const inter = localFont({
  src: [
    { path: "../node_modules/@fontsource/inter/files/inter-latin-400-normal.woff2", weight: "400", style: "normal" },
    { path: "../node_modules/@fontsource/inter/files/inter-latin-500-normal.woff2", weight: "500", style: "normal" },
    { path: "../node_modules/@fontsource/inter/files/inter-latin-600-normal.woff2", weight: "600", style: "normal" },
    { path: "../node_modules/@fontsource/inter/files/inter-latin-700-normal.woff2", weight: "700", style: "normal" },
  ],
  variable: "--font-inter",
  display: "swap",
});
