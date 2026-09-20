import { z } from "zod";

/**
 * PasswordResetRequestSchema - antrean permintaan reset password yang
 * dibuat otomatis saat staf memakai "Lupa Password" (lihat
 * app/api/auth/forgot-password/route.ts). Ini menyambungkan stub tersebut
 * ke alur nyata: karena sistem tidak punya server email, permintaan reset
 * masuk ke antrean yang HANYA bisa dilihat & ditindaklanjuti Admin Faskes
 * tempat staf tersebut terdaftar — konsisten dengan keputusan desain
 * "registrasi & reset password diurus oleh faskes, bukan self-service".
 */
export const PasswordResetRequestSchema = z.object({
  id: z.string().uuid(),
  userId: z.string().uuid(),
  userNama: z.string(),
  userEmail: z.string().email(),
  faskesId: z.string().uuid(),
  status: z.enum(["pending", "selesai"]),
  requestedAt: z.string().datetime(),
  resolvedAt: z.string().datetime().optional(),
});
export type PasswordResetRequest = z.infer<typeof PasswordResetRequestSchema>;

/** Payload Admin menyelesaikan permintaan - menetapkan password baru untuk staf terkait. */
export const ResolveResetRequestPayloadSchema = z.object({
  passwordBaru: z.string().min(8, "Password baru minimal 8 karakter"),
});
export type ResolveResetRequestPayload = z.infer<typeof ResolveResetRequestPayloadSchema>;
