import { NextResponse } from "next/server";
import { createResetRequest } from "@/lib/data/password-reset-store";
import { findUserByEmail } from "@/lib/data/user-store";
import { ForgotPasswordPayloadSchema } from "@/lib/schemas/triase.schema";

export async function POST(request: Request) {
  const body: unknown = await request.json().catch(() => null);
  const parsed = ForgotPasswordPayloadSchema.safeParse(body);

  if (!parsed.success) {
    return NextResponse.json({ error: "Format email tidak valid.", issues: parsed.error.issues }, { status: 400 });
  }

  const user = findUserByEmail(parsed.data.email);
  if (user?.isActive) {
    createResetRequest({ userId: user.id, userNama: user.nama, userEmail: user.email, faskesId: user.faskesId });
  }

  return NextResponse.json(
    { message: "Jika email tersebut terdaftar, instruksi reset password telah dikirim (simulasi)." },
    { status: 200 },
  );
}
