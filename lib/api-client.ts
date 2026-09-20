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

/**
 * Lapisan service fetch, mengikuti pola Modul 7 (src/services/taskApi.ts):
 * setiap respons API divalidasi ulang dengan Zod SEBELUM dipercaya oleh
 * TanStack Query, karena tipe TypeScript dari fetch() hanyalah janji
 * compile-time — data JSON sungguhan tetap `unknown` pada saat runtime.
 */

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

/** FR-09: mengambil daftar antrean, terurut prioritas kegawatan dari server. */
export async function fetchAntrean(): Promise<TriageRecord[]> {
  const res = await fetch("/api/triase", { method: "GET" });
  const body = await parseJsonOrThrow(res);
  return z.array(TriageRecordSchema).parse(body);
}

/** Mengambil satu record berdasarkan idTriase. */
export async function fetchTriageById(idTriase: string): Promise<TriageRecord> {
  const res = await fetch(`/api/triase/${idTriase}`, { method: "GET" });
  const body = await parseJsonOrThrow(res);
  return TriageRecordSchema.parse(body);
}

/** FR-03/04/05: submit input triase, server menjalankan classify() dan mengembalikan hasil. */
export async function submitTriase(input: TriageInput): Promise<TriageRecord> {
  const res = await fetch("/api/triase", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  const body = await parseJsonOrThrow(res);
  return TriageRecordSchema.parse(body);
}

/** FR-06/FR-07/FR-08: menyetujui, mengoreksi, atau mengajukan review hasil triase. */
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

/** Daftar staf di faskes Admin yang login (khusus role admin_faskes). */
export async function fetchStaff(): Promise<UserPublic[]> {
  const res = await fetch("/api/admin/staff", { method: "GET" });
  const body = await parseJsonOrThrow(res);
  return z.array(UserPublicSchema).parse(body);
}

/** Registrasi staf baru - hanya bisa dipanggil Admin Faskes yang login. */
export async function createStaff(input: RegisterStaffPayload): Promise<UserPublic> {
  const res = await fetch("/api/admin/staff", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  const body = await parseJsonOrThrow(res);
  return UserPublicSchema.parse(body);
}

/** Aktifkan/nonaktifkan akun staf. */
export async function toggleStaffActive(id: string, isActive: boolean): Promise<UserPublic> {
  const res = await fetch(`/api/admin/staff/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ isActive }),
  });
  const body = await parseJsonOrThrow(res);
  return UserPublicSchema.parse(body);
}

/** Edit info akun staf lain (nama, email, peran). */
export async function updateStaff(id: string, input: UpdateStaffPayload): Promise<UserPublic> {
  const res = await fetch(`/api/admin/staff/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  const body = await parseJsonOrThrow(res);
  return UserPublicSchema.parse(body);
}

/** Daftar permintaan reset password PENDING di faskes Admin yang login. */
export async function fetchPendingPasswordResets(): Promise<PasswordResetRequest[]> {
  const res = await fetch("/api/admin/password-resets", { method: "GET" });
  const body = await parseJsonOrThrow(res);
  return z.array(PasswordResetRequestSchema).parse(body);
}

/** Selesaikan permintaan reset - set password baru untuk staf terkait. */
export async function resolvePasswordReset(id: string, passwordBaru: string): Promise<PasswordResetRequest> {
  const res = await fetch(`/api/admin/password-resets/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ passwordBaru }),
  });
  const body = await parseJsonOrThrow(res);
  return PasswordResetRequestSchema.parse(body);
}

/** Update profil akun sendiri (nama, opsional password) - tersedia untuk semua role. */
export async function updateProfile(input: UpdateProfilePayload): Promise<UserPublic> {
  const res = await fetch("/api/auth/profile", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  const body = await parseJsonOrThrow(res);
  return UserPublicSchema.parse(body);
}

/** Daftar pasien terdaftar di faskes pengguna yang login. */
export async function fetchPasien(): Promise<Pasien[]> {
  const res = await fetch("/api/pasien", { method: "GET" });
  const body = await parseJsonOrThrow(res);
  return z.array(PasienSchema).parse(body);
}

/** Registrasi pasien baru. */
export async function registerPasien(input: RegisterPasienPayload): Promise<Pasien> {
  const res = await fetch("/api/pasien", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  const body = await parseJsonOrThrow(res);
  return PasienSchema.parse(body);
}

/** Riwayat triase pasien berdasarkan nama (Perawat & DPJ). */
export async function fetchRiwayatTriase(nama: string): Promise<TriageRecord[]> {
  const res = await fetch(`/api/triase/riwayat?nama=${encodeURIComponent(nama)}`, { method: "GET" });
  const body = await parseJsonOrThrow(res);
  return z.array(TriageRecordSchema).parse(body);
}

/** Konfigurasi model AI saat ini (Super Admin). */
export async function fetchAiConfig(): Promise<AiConfig> {
  const res = await fetch("/api/superadmin/konfigurasi-ai", { method: "GET" });
  const body = await parseJsonOrThrow(res);
  return AiConfigSchema.parse(body);
}

/** Update konfigurasi model AI (Super Admin). */
export async function updateAiConfig(input: AiConfig): Promise<AiConfig> {
  const res = await fetch("/api/superadmin/konfigurasi-ai", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  const body = await parseJsonOrThrow(res);
  return AiConfigSchema.parse(body);
}
