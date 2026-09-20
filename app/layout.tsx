import { Analytics } from "@vercel/analytics/next";
import { SpeedInsights } from "@vercel/speed-insights/next";
import type { Metadata } from "next";
import { inter } from "./fonts";
import { Providers } from "./providers";
import "./globals.css";

// next/font: dimensi CSS font ditetapkan eksplisit di build-time, mendukung
// CLS <= 0.1 (Modul 6, Bab F). Lihat app/fonts.ts untuk detail self-hosting.

// Metadata API statis (Modul 6, Bab F) - berlaku sebagai default untuk
// seluruh rute, bisa ditimpa oleh metadata/generateMetadata per halaman.
export const metadata: Metadata = {
  title: {
    default: "SmartTriage AI",
    template: "%s | SmartTriage AI",
  },
  description:
    "Sistem bantu triase pasien berbasis AI untuk IGD & Puskesmas — prototipe akademik D3 Teknik Informatika Sekolah Vokasi UNS.",
  keywords: ["SmartTriage AI", "UNS", "Sekolah Vokasi", "Teknik Informatika", "Next.js", "triase"],
  authors: [{ name: "Imam Abidin — D3 TI Kab. Madiun, Sekolah Vokasi UNS" }],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="id" className={inter.variable}>
      <body className="min-h-screen font-sans antialiased">
        <Providers>{children}</Providers>
        {/* Bab J: Core Web Vitals - mengumpulkan LCP/INP/CLS field data
            sungguhan dari pengunjung nyata (metodologi CrUX) begitu
            aplikasi live di Vercel, terlihat di dashboard Vercel >
            Speed Insights. Kedua komponen memuat skrip & mengirim data
            lewat path same-origin /_vercel/* (bukan domain pihak
            ketiga) - selaras dengan Content-Security-Policy ketat di
            next.config.ts tanpa perlu pengecualian tambahan. */}
        <SpeedInsights />
        <Analytics />
      </body>
    </html>
  );
}
