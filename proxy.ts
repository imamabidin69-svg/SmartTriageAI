import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { SESSION_COOKIE } from "@/lib/constants";
import { getHomeRouteForRole } from "@/lib/role-routes";

/**
 * proxy.ts - Server-Side Access Control & Route Guard (Modul 6, poin F).
 * Sebelumnya bernama middleware.ts — konvensi ini di-rename oleh Next.js
 * (dimigrasikan otomatis lewat `npx @next/codemod middleware-to-proxy`),
 * perilaku dan API-nya identik, hanya nama file & fungsi ekspornya yang
 * berubah. Dieksekusi di server SEBELUM request mencapai komponen halaman
 * manapun. Sengaja hanya memeriksa KEBERADAAN cookie sesi (bukan
 * memvalidasi isi lengkapnya dengan Zod) karena Edge Runtime tempat proxy
 * berjalan membatasi beberapa API Node.js — validasi isi penuh tetap
 * dilakukan lewat getSession() di Server Component/Route Handler.
 */
const PROTECTED_PREFIXES = [
  "/dashboard",
  "/triase",
  "/admin",
  "/pasien",
  "/riwayat-pasien",
  "/asesmen-visual",
  "/superadmin",
  "/auditor",
  "/dinas-kesehatan",
  "/profil",
];

export function proxy(request: NextRequest) {
  const sessionCookie = request.cookies.get(SESSION_COOKIE)?.value;
  const isProtectedRoute = PROTECTED_PREFIXES.some((p) => request.nextUrl.pathname.startsWith(p));

  if (isProtectedRoute && !sessionCookie) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("auth_error", "1");
    return NextResponse.redirect(loginUrl);
  }

  // Pengguna yang sudah login tidak perlu melihat halaman login lagi.
  // Sengaja HANYA memeriksa keberadaan cookie (bukan membaca/memverifikasi
  // isinya) — sejak cookie sesi ditandatangani HMAC (lib/session-cookie.ts),
  // Edge Runtime di sini tidak mendukung node:crypto sinkron untuk
  // memverifikasinya. Ini bukan celah keamanan: proxy TIDAK PERNAH
  // dipakai sebagai boundary otorisasi sungguhan (itu tugas getSession()
  // penuh di Server Component/Route Handler) — ini murni kenyamanan UX
  // supaya pengguna yang sudah login tidak disodori halaman login lagi.
  // Redirect selalu ke "/dashboard" (getHomeRouteForRole tanpa role
  // diketahui); jika peran sebenarnya butuh halaman lain, "/" akan
  // meneruskannya dengan benar via getSession() penuh di sisi server.
  if (request.nextUrl.pathname === "/login" && sessionCookie) {
    return NextResponse.redirect(new URL(getHomeRouteForRole(undefined), request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/triase/:path*",
    "/admin/:path*",
    "/pasien/:path*",
    "/riwayat-pasien/:path*",
    "/asesmen-visual/:path*",
    "/superadmin/:path*",
    "/auditor/:path*",
    "/dinas-kesehatan/:path*",
    "/profil/:path*",
    "/login",
  ],
};
