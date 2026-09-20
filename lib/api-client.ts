import { z } from "zod";
import { type AiConfig, AiConfigSchema } from "@/lib/schemas/ai-config.schema";
import { type Pasien, PasienSchema, type RegisterPasienPayload } from "@/lib/schemas/pasien.schema";
import { type PasswordResetRequest, PasswordResetRequestSchema } from "@/lib/schemas/password-reset.schema";
import {
  type RegisterStaffPayload,
  type TriageInput,
  type TriageRecord,
  TriageRecordSchema,
  type UpdateProfilePayload,
  type UpdateStaffPayload,
  type UserPublic,
  UserPublicSchema,
  type ValidasiTriase,
  ValidasiTriaseSchema,
} from "@/lib/schemas/triase.schema";

async function parseJsonOrThrow(response: Response): Promise<unknown> {
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const message =
      body && typeof body === "object" && "error" in body && typeof body.error === "string"
        ? body.error
        : `Permintaan gagal (HTTP ${response.status})`;
    throw new Error(message);
  }
  return body;
}

export async function fetchAntrean(): Promise<TriageRecord[]> {
  const res = await fetch("/api/triase", { method: "GET" });
  const body = await parseJsonOrThrow(res);
  return z.array(TriageRecordSchema).parse(body);
}

export async function fetchTriageById(idTriase: string): Promise<TriageRecord> {
  const res = await fetch(`/api/triase/${idTriase}`, { method: "GET" });
  const body = await parseJsonOrThrow(res);
  return TriageRecordSchema.parse(body);
}

export async function submitTriase(input: TriageInput): Promise<TriageRecord> {
  const res = await fetch("/api/triase", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  const body = await parseJsonOrThrow(res);
  return TriageRecordSchema.parse(body);
}

export async function submitValidasi(payload: ValidasiTriase): Promise<TriageRecord> {
  ValidasiTriaseSchema.parse(payload); // validasi sisi klien sebelum kirim (fail-fast)
  const res = await fetch(`/api/triase/${payload.idTriase}/validasi`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body = await parseJsonOrThrow(res);
  return TriageRecordSchema.parse(body);
}

export async function fetchStaff(): Promise<UserPublic[]> {
  const res = await fetch("/api/admin/staff", { method: "GET" });
  const body = await parseJsonOrThrow(res);
  return z.array(UserPublicSchema).parse(body);
}

export async function createStaff(input: RegisterStaffPayload): Promise<UserPublic> {
  const res = await fetch("/api/admin/staff", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  const body = await parseJsonOrThrow(res);
  return UserPublicSchema.parse(body);
}

export async function toggleStaffActive(id: string, isActive: boolean): Promise<UserPublic> {
  const res = await fetch(`/api/admin/staff/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ isActive }),
  });
  const body = await parseJsonOrThrow(res);
  return UserPublicSchema.parse(body);
}

export async function updateStaff(id: string, input: UpdateStaffPayload): Promise<UserPublic> {
  const res = await fetch(`/api/admin/staff/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  const body = await parseJsonOrThrow(res);
  return UserPublicSchema.parse(body);
}

export async function fetchPendingPasswordResets(): Promise<PasswordResetRequest[]> {
  const res = await fetch("/api/admin/password-resets", { method: "GET" });
  const body = await parseJsonOrThrow(res);
  return z.array(PasswordResetRequestSchema).parse(body);
}

export async function resolvePasswordReset(id: string, passwordBaru: string): Promise<PasswordResetRequest> {
  const res = await fetch(`/api/admin/password-resets/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ passwordBaru }),
  });
  const body = await parseJsonOrThrow(res);
  return PasswordResetRequestSchema.parse(body);
}

export async function updateProfile(input: UpdateProfilePayload): Promise<UserPublic> {
  const res = await fetch("/api/auth/profile", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  const body = await parseJsonOrThrow(res);
  return UserPublicSchema.parse(body);
}

export async function fetchPasien(): Promise<Pasien[]> {
  const res = await fetch("/api/pasien", { method: "GET" });
  const body = await parseJsonOrThrow(res);
  return z.array(PasienSchema).parse(body);
}

export async function registerPasien(input: RegisterPasienPayload): Promise<Pasien> {
  const res = await fetch("/api/pasien", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  const body = await parseJsonOrThrow(res);
  return PasienSchema.parse(body);
}

export async function fetchRiwayatTriase(nama: string): Promise<TriageRecord[]> {
  const res = await fetch(`/api/triase/riwayat?nama=${encodeURIComponent(nama)}`, { method: "GET" });
  const body = await parseJsonOrThrow(res);
  return z.array(TriageRecordSchema).parse(body);
}

export async function fetchAiConfig(): Promise<AiConfig> {
  const res = await fetch("/api/superadmin/konfigurasi-ai", { method: "GET" });
  const body = await parseJsonOrThrow(res);
  return AiConfigSchema.parse(body);
}

export async function updateAiConfig(input: AiConfig): Promise<AiConfig> {
  const res = await fetch("/api/superadmin/konfigurasi-ai", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  const body = await parseJsonOrThrow(res);
  return AiConfigSchema.parse(body);
}
