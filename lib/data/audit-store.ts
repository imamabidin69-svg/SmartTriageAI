import "server-only";
import type { AuditLogEntry } from "@/lib/schemas/audit.schema";

const entries: AuditLogEntry[] = [];

export function appendAuditLog(entry: AuditLogEntry): void {
  entries.push(entry);
}

export function listAllAuditLog(): AuditLogEntry[] {
  return [...entries].sort((a, b) => b.waktu.localeCompare(a.waktu));
}
