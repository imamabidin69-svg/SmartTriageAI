import { Analytics } from "@vercel/analytics/next";
import { SpeedInsights } from "@vercel/speed-insights/next";
import type { Metadata, Viewport } from "next";
import { UI_PREFERENCES_KEY } from "@/lib/constants";
import { inter } from "./fonts";
import { Providers } from "./providers";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "SmartTriage AI",
    template: "%s | SmartTriage AI",
  },
  description:
    "Sistem bantu triase pasien berbasis AI untuk IGD & Puskesmas, prototipe akademik D3 Teknik Informatika Sekolah Vokasi UNS.",
  keywords: ["SmartTriage AI", "UNS", "Sekolah Vokasi", "Teknik Informatika", "Next.js", "triase"],
  authors: [{ name: "Imam Abidin, D3 TI Kab. Madiun, Sekolah Vokasi UNS" }],
};

export const viewport: Viewport = {
  colorScheme: "light dark",
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f8fafc" },
    { media: "(prefers-color-scheme: dark)", color: "#0f172a" },
  ],
};

// Jalan sebelum halaman digambar supaya pengguna mode gelap tidak melihat kilasan putih.
// "light"/"dark" = dikunci pengguna; selain itu ikut preferensi sistem.
const THEME_INIT_SCRIPT = `(function(){try{var m=null;var s=localStorage.getItem(${JSON.stringify(
  UI_PREFERENCES_KEY,
)});if(s){var p=JSON.parse(s);m=p&&p.state?p.state.themeMode:null}var r=document.documentElement;if(m==="light"){r.classList.add("light")}else if(m==="dark"||window.matchMedia("(prefers-color-scheme: dark)").matches){r.classList.add("dark")}}catch(e){}})();`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="id" className={inter.variable} suppressHydrationWarning>
      <head>
        {/* biome-ignore lint/security/noDangerouslySetInnerHtml: skrip statis milik sendiri, harus inline agar jalan sebelum paint */}
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
      </head>
      <body className="min-h-dvh font-sans antialiased">
        <a
          href="#konten-utama"
          className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-(--z-toast) focus:rounded-lg focus:bg-white focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-blue-700 focus:shadow-lg focus:ring-2 focus:ring-blue-500 dark:focus:bg-slate-800 dark:focus:text-blue-300"
        >
          Lewati ke konten utama
        </a>
        <Providers>{children}</Providers>
        <SpeedInsights />
        <Analytics />
      </body>
    </html>
  );
}
