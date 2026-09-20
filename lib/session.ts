import "server-only";
import { cookies } from "next/headers";
import { SESSION_COOKIE } from "@/lib/constants";
import { type Faskes, type Session, SessionSchema, type User } from "@/lib/schemas/triase.schema";
import { verifySessionCookie } from "@/lib/session-cookie";

export { SESSION_COOKIE };

export function createSessionForUser(user: User, faskes: Faskes): Session {
  return SessionSchema.parse({
    userId: user.id,
    nama: user.nama,
    role: user.role,
    faskesId: user.faskesId,
    faskesNama: faskes.nama,
  });
}

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

export function canOverride(session: Session | null): boolean {
  return session?.role === "dokter_pj";
}
