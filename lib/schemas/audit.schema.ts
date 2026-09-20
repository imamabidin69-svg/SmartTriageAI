import { z } from "zod";
import { RiskLevelSchema } from "@/lib/schemas/triase.schema";

/**
 * AuditLogEntrySchema - mencatat aksi-aksi penting lintas-modul sebagai
 * jejak audit tunggal, terpisah dari data operasionalnya sendiri (TriageRecord,
 * User, Pasien). Dipakai oleh peran Auditor (lintas-faskes, read-only).
 *
 * Diperluas dari versi awal (yang hanya mencatat Setujui/Koreksi/Ajukan
 * Review) untuk juga mencakup manajemen akun staf dan registrasi pasien —
 * supaya Auditor benar-benar bisa melihat "siapa melakukan apa" secara
 * menyeluruh, bukan cuma jejak validasi triase.
 */
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
  /** Nama objek yang terkena aksi - nama pasien (aksi triase) ATAU nama staf (aksi akun). */
  targetNama: z.string(),
  catatan: z.string().optional(),
  /** Hanya diisi untuk aksi terkait triase (setujui/koreksi/ajukan_review). */
  idTriase: z.string().uuid().optional(),
  riskLevelSebelum: RiskLevelSchema.optional(),
  riskLevelSesudah: RiskLevelSchema.optional(),
  waktu: z.string().datetime(),
});
export type AuditLogEntry = z.infer<typeof AuditLogEntrySchema>;
