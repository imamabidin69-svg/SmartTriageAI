import { NextResponse } from "next/server";
import { getRequestById, markResolved } from "@/lib/data/password-reset-store";
import { setUserPasswordHash } from "@/lib/data/user-store";
import { hashPassword } from "@/lib/password";
import { ResolveResetRequestPayloadSchema } from "@/lib/schemas/password-reset.schema";
import { getSession } from "@/lib/session";

/**
 * PATCH /api/admin/password-resets/[id] - Admin Faskes menetapkan password
 * baru untuk staf yang mengajukan permintaan, lalu menandai permintaan
 * selesai. Dua langkah ini dijalankan sebagai satu aksi tunggal dari sisi
 * Admin (form "Reset Password" di StaffManagementClient) supaya alurnya
 * sesederhana mungkin bagi Admin yang menindaklanjuti manual.
 */
export async function PATCH(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const session = await getSession();
  if (!session) {
    return NextResponse.json({ error: "Sesi tidak ditemukan. Silakan masuk kembali." }, { status: 401 });
  }
  if (session.role !== "admin_faskes") {
    return NextResponse.json(
      { error: "Hanya Admin Faskes yang berwenang menyelesaikan permintaan ini." },
      { status: 403 },
    );
  }

  const { id } = await params;
  const existingRequest = getRequestById(id);
  if (!existingRequest || existingRequest.faskesId !== session.faskesId) {
    return NextResponse.json({ error: "Permintaan tidak ditemukan di faskes Anda." }, { status: 404 });
  }
  if (existingRequest.status === "selesai") {
    return NextResponse.json({ error: "Permintaan ini sudah diselesaikan sebelumnya." }, { status: 409 });
  }

  const body: unknown = await request.json().catch(() => null);
  const parsed = ResolveResetRequestPayloadSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json({ error: "Password baru tidak valid.", issues: parsed.error.issues }, { status: 400 });
  }

  const updatedUser = setUserPasswordHash(
    existingRequest.userId,
    session.faskesId,
    hashPassword(parsed.data.passwordBaru),
  );
  if (!updatedUser) {
    return NextResponse.json({ error: "Akun staf terkait tidak ditemukan." }, { status: 404 });
  }

  const resolved = markResolved(id, session.faskesId);
  return NextResponse.json(resolved, { status: 200 });
}
