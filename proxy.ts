import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { SESSION_COOKIE } from "@/lib/constants";
import { getHomeRouteForRole } from "@/lib/role-routes";

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
