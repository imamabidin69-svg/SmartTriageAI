import { NextResponse } from "next/server";
import { appendAuditLog } from "@/lib/data/audit-store";
import { emailExists, insertUser, listStaffByFaskes } from "@/lib/data/user-store";
import { hashPassword } from "@/lib/password";
import { RegisterStaffPayloadSchema, type UserPublic, UserPublicSchema } from "@/lib/schemas/triase.schema";
import { getSession } from "@/lib/session";

function toPublic(user: { passwordHash: string; [k: string]: unknown }): UserPublic {
  const { passwordHash: _passwordHash, ...rest } = user;
  return UserPublicSchema.parse(rest);
}

export async function GET() {
  const session = await getSession();
  if (!session) {
    return NextResponse.json({ error: "Sesi tidak ditemukan. Silakan masuk kembali." }, { status: 401 });
  }
  if (session.role !== "admin_faskes") {
    return NextResponse.json({ error: "Hanya Admin Faskes yang berwenang mengelola akun staf." }, { status: 403 });
  }

  const staff = listStaffByFaskes(session.faskesId).map(toPublic);
  return NextResponse.json(staff, { status: 200 });
}

export async function POST(request: Request) {
  const session = await getSession();
  if (!session) {
    return NextResponse.json({ error: "Sesi tidak ditemukan. Silakan masuk kembali." }, { status: 401 });
  }
  if (session.role !== "admin_faskes") {
    return NextResponse.json({ error: "Hanya Admin Faskes yang berwenang mendaftarkan akun staf." }, { status: 403 });
  }

  const body: unknown = await request.json().catch(() => null);
  const parsed = RegisterStaffPayloadSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json({ error: "Data registrasi tidak valid.", issues: parsed.error.issues }, { status: 400 });
  }

  if (emailExists(parsed.data.email)) {
    return NextResponse.json({ error: "Email tersebut sudah terdaftar." }, { status: 409 });
  }

  const newUser = {
    id: crypto.randomUUID(),
    nama: parsed.data.nama,
    email: parsed.data.email,
    passwordHash: hashPassword(parsed.data.password),
    role: parsed.data.role,
    faskesId: session.faskesId,
    isActive: true,
    createdAt: new Date().toISOString(),
  };

  insertUser(newUser);

  appendAuditLog({
    id: crypto.randomUUID(),
    faskesId: session.faskesId,
    faskesNama: session.faskesNama,
    aksi: "staf_dibuat",
    aktorUserId: session.userId,
    aktorNama: session.nama,
    targetNama: newUser.nama,
    catatan: `Peran: ${newUser.role}`,
    waktu: new Date().toISOString(),
  });

  return NextResponse.json(toPublic(newUser), { status: 201 });
}
