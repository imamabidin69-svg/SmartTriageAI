import "server-only";
import { cookies } from "next/headers";
import { SESSION_COOKIE } from "@/lib/constants";
import { type Faskes, type Session, SessionSchema, type User } from "@/lib/schemas/triase.schema";
import { verifySessionCookie } from "@/lib/session-cookie";

export { SESSION_COOKIE };

/** Membentuk objek sesi baru (FR-01) dari User & Faskes yang berhasil diautentikasi. */
export function createSessionForUser(user: User, faskes: Faskes): Session {
  return SessionSchema.parse({
    userId: user.id,
    nama: user.nama,
    role: user.role,
    faskesId: user.faskesId,
    faskesNama: faskes.nama,
  });
}

/**
 * Membaca sesi dari cookie httpOnly di sisi SERVER (Server Component, Route
 * Handler, atau Proxy). Tanda tangan HMAC diverifikasi TERLEBIH DAHULU
 * (lihat lib/session-cookie.ts) sebelum payload dipercaya untuk di-parse —
 * cookie yang diedit manual lewat DevTools akan gagal verifikasi dan
 * dianggap tidak ada sesi sama sekali. Setelah itu tetap divalidasi ulang
 * lewat SessionSchema sebagai lapis pertahanan kedua.
 */
export async function getSession(): Promise<Session | null> {
  const store = await cookies();
  const raw = store.get(SESSION_COOKIE)?.value;
  if (!raw) return null;

  const verifiedJson = verifySessionCookie(raw);
  if (!verifiedJson) return null;

  try {
    const parsed: unknown = JSON.parse(verifiedJson);
    const result = SessionSchema.safeParse(parsed);
    return result.success ? result.data : null;
  } catch {
    return null;
  }
}

/** Wewenang override/koreksi hasil AI hanya milik DPJ (lihat NFR-06 & FR-07). */
export function canOverride(session: Session | null): boolean {
  return session?.role === "dokter_pj";
}
