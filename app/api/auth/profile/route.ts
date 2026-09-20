import { NextResponse } from "next/server";
import { SESSION_COOKIE } from "@/lib/constants";
import { getFaskesById, getUserById, updateOwnProfile } from "@/lib/data/user-store";
import { hashPassword, verifyPassword } from "@/lib/password";
import { UpdateProfilePayloadSchema, type UserPublic, UserPublicSchema } from "@/lib/schemas/triase.schema";
import { createSessionForUser, getSession } from "@/lib/session";
import { signSessionCookie } from "@/lib/session-cookie";

function toPublic(user: { passwordHash: string; [k: string]: unknown }): UserPublic {
  const { passwordHash: _passwordHash, ...rest } = user;
  return UserPublicSchema.parse(rest);
}

/** GET /api/auth/profile - data profil pengguna yang sedang login. */
export async function GET() {
  const session = await getSession();
  if (!session) {
    return NextResponse.json({ error: "Sesi tidak ditemukan. Silakan masuk kembali." }, { status: 401 });
  }
  const user = getUserById(session.userId);
  if (!user) {
    return NextResponse.json({ error: "Akun tidak ditemukan." }, { status: 404 });
  }
  return NextResponse.json(toPublic(user), { status: 200 });
}

/**
 * PATCH /api/auth/profile - ubah nama dan/atau password akun SENDIRI.
 * Tersedia untuk semua role (bukan cuma Admin Faskes) — setiap pengguna
 * berhak mengelola profilnya sendiri. Mengganti password wajib membuktikan
 * tahu password lama (passwordSaatIni) walau sudah dalam sesi
 * terautentikasi, sebagai pertahanan berlapis.
 */
export async function PATCH(request: Request) {
  const session = await getSession();
  if (!session) {
    return NextResponse.json({ error: "Sesi tidak ditemukan. Silakan masuk kembali." }, { status: 401 });
  }

  const body: unknown = await request.json().catch(() => null);
  const parsed = UpdateProfilePayloadSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { error: parsed.error.issues[0]?.message ?? "Data profil tidak valid.", issues: parsed.error.issues },
      { status: 400 },
    );
  }

  const user = getUserById(session.userId);
  if (!user) {
    return NextResponse.json({ error: "Akun tidak ditemukan." }, { status: 404 });
  }

  let newPasswordHash: string | undefined;
  if (parsed.data.passwordBaru) {
    if (!parsed.data.passwordSaatIni || !verifyPassword(parsed.data.passwordSaatIni, user.passwordHash)) {
      return NextResponse.json({ error: "Password saat ini salah." }, { status: 403 });
    }
    newPasswordHash = hashPassword(parsed.data.passwordBaru);
  }

  const updated = updateOwnProfile(user.id, { nama: parsed.data.nama, passwordHash: newPasswordHash });
  if (!updated) {
    return NextResponse.json({ error: "Gagal memperbarui profil." }, { status: 500 });
  }

  const faskes = getFaskesById(updated.faskesId);
  if (!faskes) {
    return NextResponse.json({ error: "Data faskes untuk akun ini tidak ditemukan." }, { status: 500 });
  }

  // Nama bisa berubah -> sinkronkan ulang cookie sesi supaya header langsung menampilkan nama terbaru.
  const newSession = createSessionForUser(updated, faskes);
  const response = NextResponse.json(toPublic(updated), { status: 200 });
  response.cookies.set(SESSION_COOKIE, signSessionCookie(JSON.stringify(newSession)), {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 8,
  });
  return response;
}
