import "server-only";
import type { AuditLogEntry } from "@/lib/schemas/audit.schema";

const entries: AuditLogEntry[] = [];

export function appendAuditLog(entry: AuditLogEntry): void {
  entries.push(entry);
}

/** Auditor bersifat lintas-faskes (lihat tabel aktor SRS), jadi tanpa filter faskesId. */
export function listAllAuditLog(): AuditLogEntry[] {
  return [...entries].sort((a, b) => b.waktu.localeCompare(a.waktu));
}
