import { z } from "zod";

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

export const ResolveResetRequestPayloadSchema = z.object({
  passwordBaru: z.string().min(8, "Password baru minimal 8 karakter"),
});
export type ResolveResetRequestPayload = z.infer<typeof ResolveResetRequestPayloadSchema>;
