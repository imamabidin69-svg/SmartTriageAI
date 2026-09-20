import type { NextConfig } from "next";

/**
 * Security headers - Bab K: Keamanan Sisi Klien & Mitigasi OWASP
 * Client-Side. Diterapkan lewat headers() supaya berlaku di SELURUH rute
 * tanpa perlu diulang manual per Route Handler.
 *
 * Catatan jujur soal CSP: script-src masih menyertakan 'unsafe-inline'
 * karena Next.js App Router menyuntikkan skrip bootstrap hidrasi inline
 * (payload RSC) yang, tanpa penyiapan nonce per-request (di luar cakupan
 * waktu pengerjaan saat ini), akan diblokir oleh CSP yang benar-benar
 * ketat dan merusak aplikasi. Proteksi yang paling relevan untuk ancaman
 * OWASP di sini (clickjacking via frame-ancestors, pemuatan objek/plugin
 * asing, MIME-sniffing) tetap aktif penuh.
 */
const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
  {
    key: "Content-Security-Policy",
    value: [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline'",
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data:",
      "font-src 'self'",
      "connect-src 'self'",
      "object-src 'none'",
      "base-uri 'self'",
      "frame-ancestors 'none'",
    ].join("; "),
  },
];

const nextConfig: NextConfig = {
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
};

export default nextConfig;
