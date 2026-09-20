import { NextResponse } from "next/server";
import { createResetRequest } from "@/lib/data/password-reset-store";
import { findUserByEmail } from "@/lib/data/user-store";
import { ForgotPasswordPayloadSchema } from "@/lib/schemas/triase.schema";

/**
 * POST /api/auth/forgot-password - menyambungkan stub "lupa password" ke
 * antrean nyata yang dilihat Admin Faskes (lihat lib/data/password-reset-store.ts).
 * Sistem ini tidak punya server email sungguhan, jadi TIDAK ada email yang
 * benar-benar terkirim — sebagai gantinya, permintaan masuk ke antrean yang
 * HANYA bisa ditindaklanjuti Admin Faskes tempat staf tersebut terdaftar.
 *
 * Selalu mengembalikan pesan sukses generik yang SAMA baik email terdaftar
 * maupun tidak (mencegah user enumeration — praktik keamanan standar).
 * Permintaan HANYA benar-benar dibuat jika email ditemukan & akun aktif,
 * tapi respons ke pemanggil tidak pernah membocorkan informasi itu.
 */
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
