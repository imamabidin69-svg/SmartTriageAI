import { NextResponse } from "next/server";
import { z } from "zod";
import { appendAuditLog } from "@/lib/data/audit-store";
import { emailExistsExcluding, setUserActive, updateStaffInfo } from "@/lib/data/user-store";
import { UpdateStaffPayloadSchema, type UserPublic, UserPublicSchema } from "@/lib/schemas/triase.schema";
import { getSession } from "@/lib/session";

const ToggleActivePayloadSchema = z.object({ isActive: z.boolean() });

function toPublic(user: { passwordHash: string; [k: string]: unknown }): UserPublic {
  const { passwordHash: _passwordHash, ...rest } = user;
  return UserPublicSchema.parse(rest);
}

export async function PATCH(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const session = await getSession();
  if (!session) {
    return NextResponse.json({ error: "Sesi tidak ditemukan. Silakan masuk kembali." }, { status: 401 });
  }
  if (session.role !== "admin_faskes") {
    return NextResponse.json({ error: "Hanya Admin Faskes yang berwenang mengelola akun staf." }, { status: 403 });
  }

  const { id } = await params;
  if (id === session.userId) {
    return NextResponse.json(
      { error: "Anda tidak bisa mengubah akun Anda sendiri lewat halaman ini." },
      { status: 400 },
    );
  }

  const body: unknown = await request.json().catch(() => null);

  const togglePaylod = ToggleActivePayloadSchema.safeParse(body);
  if (togglePaylod.success) {
    const updated = setUserActive(id, session.faskesId, togglePaylod.data.isActive);
    if (!updated) {
      return NextResponse.json({ error: "Akun staf tidak ditemukan di faskes Anda." }, { status: 404 });
    }
    appendAuditLog({
      id: crypto.randomUUID(),
      faskesId: session.faskesId,
      faskesNama: session.faskesNama,
      aksi: togglePaylod.data.isActive ? "staf_diaktifkan" : "staf_dinonaktifkan",
      aktorUserId: session.userId,
      aktorNama: session.nama,
      targetNama: updated.nama,
      waktu: new Date().toISOString(),
    });
    return NextResponse.json(toPublic(updated), { status: 200 });
  }

  const editPayload = UpdateStaffPayloadSchema.safeParse(body);
  if (!editPayload.success) {
    return NextResponse.json({ error: "Payload tidak valid.", issues: editPayload.error.issues }, { status: 400 });
  }

  if (emailExistsExcluding(editPayload.data.email, id)) {
    return NextResponse.json({ error: "Email tersebut sudah dipakai akun lain." }, { status: 409 });
  }

  const updated = updateStaffInfo(id, session.faskesId, editPayload.data);
  if (!updated) {
    return NextResponse.json({ error: "Akun staf tidak ditemukan di faskes Anda." }, { status: 404 });
  }

  appendAuditLog({
    id: crypto.randomUUID(),
    faskesId: session.faskesId,
    faskesNama: session.faskesNama,
    aksi: "staf_diedit",
    aktorUserId: session.userId,
    aktorNama: session.nama,
    targetNama: updated.nama,
    catatan: `Email: ${updated.email}, Peran: ${updated.role}`,
    waktu: new Date().toISOString(),
  });

  return NextResponse.json(toPublic(updated), { status: 200 });
}
