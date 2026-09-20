import { Analytics } from "@vercel/analytics/next";
import { SpeedInsights } from "@vercel/speed-insights/next";
import type { Metadata } from "next";
import { inter } from "./fonts";
import { Providers } from "./providers";
import "./globals.css";

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
        {}
        <SpeedInsights />
        <Analytics />
      </body>
    </html>
  );
}
