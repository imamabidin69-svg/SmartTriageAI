import { NextResponse } from "next/server";
import { SESSION_COOKIE } from "@/lib/constants";
import { findUserByEmail, getFaskesById } from "@/lib/data/user-store";
import { verifyPassword } from "@/lib/password";
import { checkRateLimit, getClientIp, resetRateLimit } from "@/lib/rate-limit";
import { LoginPayloadSchema } from "@/lib/schemas/triase.schema";
import { createSessionForUser } from "@/lib/session";
import { signSessionCookie } from "@/lib/session-cookie";

/**
 * POST /api/auth/login - FR-01, autentikasi email+password sungguhan.
 * Pesan error SENGAJA dibuat generik ("email atau password salah") baik
 * untuk email tidak terdaftar maupun password salah — supaya penyerang
 * tidak bisa menebak email mana saja yang terdaftar di sistem (praktik umum
 * keamanan autentikasi, mencegah user enumeration).
 *
 * Dibatasi rate limit (5 percobaan / 15 menit per kombinasi IP+email) untuk
 * mitigasi brute-force (Bab K: Keamanan Sisi Klien & OWASP Client-Side).
 */
export async function POST(request: Request) {
  const body: unknown = await request.json().catch(() => null);
  const parsed = LoginPayloadSchema.safeParse(body);

  if (!parsed.success) {
    return NextResponse.json(
      { error: "Email atau password tidak valid.", issues: parsed.error.issues },
      { status: 400 },
    );
  }

  const rateLimitKey = `${getClientIp(request)}:${parsed.data.email.toLowerCase()}`;
  const rateLimit = checkRateLimit(rateLimitKey);
  if (!rateLimit.allowed) {
    return NextResponse.json(
      { error: `Terlalu banyak percobaan gagal. Coba lagi dalam ${rateLimit.retryAfterSeconds} detik.` },
      { status: 429, headers: { "Retry-After": String(rateLimit.retryAfterSeconds) } },
    );
  }

  const user = findUserByEmail(parsed.data.email);
  const GENERIC_ERROR = "Email atau password salah.";

  if (!user) {
    return NextResponse.json({ error: GENERIC_ERROR }, { status: 401 });
  }
  if (!user.isActive) {
    return NextResponse.json({ error: "Akun ini telah dinonaktifkan. Hubungi Admin Faskes Anda." }, { status: 403 });
  }
  if (!verifyPassword(parsed.data.password, user.passwordHash)) {
    return NextResponse.json({ error: GENERIC_ERROR }, { status: 401 });
  }

  resetRateLimit(rateLimitKey);

  const faskes = getFaskesById(user.faskesId);
  if (!faskes) {
    return NextResponse.json({ error: "Data faskes untuk akun ini tidak ditemukan." }, { status: 500 });
  }

  const session = createSessionForUser(user, faskes);
  const response = NextResponse.json(session, { status: 200 });
  response.cookies.set(SESSION_COOKIE, signSessionCookie(JSON.stringify(session)), {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 8, // 8 jam
  });
  return response;
}
