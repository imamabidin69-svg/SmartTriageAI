import { z } from "zod";
import { RiskLevelSchema } from "@/lib/schemas/triase.schema";

export const AuditActionSchema = z.enum([
  "setujui",
  "koreksi",
  "ajukan_review",
  "staf_dibuat",
  "staf_diedit",
  "staf_diaktifkan",
  "staf_dinonaktifkan",
  "pasien_didaftarkan",
]);
export type AuditAction = z.infer<typeof AuditActionSchema>;

export const AuditLogEntrySchema = z.object({
  id: z.string().uuid(),
  faskesId: z.string().uuid(),
  faskesNama: z.string(),
  aksi: AuditActionSchema,
  aktorUserId: z.string().uuid(),
  aktorNama: z.string(),
  targetNama: z.string(),
  catatan: z.string().optional(),
  idTriase: z.string().uuid().optional(),
  riskLevelSebelum: RiskLevelSchema.optional(),
  riskLevelSesudah: RiskLevelSchema.optional(),
  waktu: z.string().datetime(),
});
export type AuditLogEntry = z.infer<typeof AuditLogEntrySchema>;
