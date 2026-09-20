import "server-only";
import type { PasswordResetRequest } from "@/lib/schemas/password-reset.schema";

/**
 * In-memory store untuk antrean permintaan reset password - sama seperti
 * lib/data/triase-store.ts & user-store.ts, reset saat server di-restart.
 */
const requests: PasswordResetRequest[] = [];

/** Dipanggil dari Route Handler forgot-password saat email DITEMUKAN & akun aktif. */
export function createResetRequest(params: {
  userId: string;
  userNama: string;
  userEmail: string;
  faskesId: string;
}): void {
  requests.push({
    id: crypto.randomUUID(),
    userId: params.userId,
    userNama: params.userNama,
    userEmail: params.userEmail,
    faskesId: params.faskesId,
    status: "pending",
    requestedAt: new Date().toISOString(),
  });
}

export function listPendingByFaskes(faskesId: string): PasswordResetRequest[] {
  return requests
    .filter((r) => r.faskesId === faskesId && r.status === "pending")
    .sort((a, b) => a.requestedAt.localeCompare(b.requestedAt));
}

export function getRequestById(id: string): PasswordResetRequest | null {
  return requests.find((r) => r.id === id) ?? null;
}

export function markResolved(id: string, faskesId: string): PasswordResetRequest | null {
  const idx = requests.findIndex((r) => r.id === id && r.faskesId === faskesId);
  if (idx === -1) return null;
  const existing = requests[idx];
  if (!existing) return null;
  const updated: PasswordResetRequest = { ...existing, status: "selesai", resolvedAt: new Date().toISOString() };
  requests[idx] = updated;
  return updated;
}
