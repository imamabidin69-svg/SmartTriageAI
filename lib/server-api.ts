import "server-only";
import { z } from "zod";
import { type AiConfig, AiConfigSchema } from "@/lib/schemas/ai-config.schema";
import { type AuditLogEntry, AuditLogEntrySchema } from "@/lib/schemas/audit.schema";
import { type Pasien, PasienSchema } from "@/lib/schemas/pasien.schema";
import {
  type FaskesRingkasan,
  FaskesRingkasanSchema,
  type RingkasanFaskes,
  RingkasanFaskesSchema,
  type TriageRecord,
  TriageRecordSchema,
  type UserPublic,
  UserPublicSchema,
} from "@/lib/schemas/triase.schema";
import { serverFetch } from "@/lib/server-fetch";

export async function fetchAntreanServer(): Promise<TriageRecord[]> {
  const res = await serverFetch("/api/triase");
  if (!res.ok) throw new Error(`Gagal memuat antrean (HTTP ${res.status})`);
  const body: unknown = await res.json();
  return z.array(TriageRecordSchema).parse(body);
}

export async function fetchTriageByIdServer(id: string): Promise<TriageRecord | null> {
  const res = await serverFetch(`/api/triase/${id}`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`Gagal memuat data triase (HTTP ${res.status})`);
  const body: unknown = await res.json();
  return TriageRecordSchema.parse(body);
}

export async function fetchStaffServer(): Promise<UserPublic[]> {
  const res = await serverFetch("/api/admin/staff");
  if (!res.ok) throw new Error(`Gagal memuat daftar staf (HTTP ${res.status})`);
  const body: unknown = await res.json();
  return z.array(UserPublicSchema).parse(body);
}

export async function fetchPasienServer(): Promise<Pasien[]> {
  const res = await serverFetch("/api/pasien");
  if (!res.ok) throw new Error(`Gagal memuat daftar pasien (HTTP ${res.status})`);
  const body: unknown = await res.json();
  return z.array(PasienSchema).parse(body);
}

export async function fetchFaskesRingkasanServer(): Promise<FaskesRingkasan[]> {
  const res = await serverFetch("/api/superadmin/faskes");
  if (!res.ok) throw new Error(`Gagal memuat data faskes (HTTP ${res.status})`);
  const body: unknown = await res.json();
  return z.array(FaskesRingkasanSchema).parse(body);
}

export async function fetchAuditLogServer(): Promise<AuditLogEntry[]> {
  const res = await serverFetch("/api/auditor/log");
  if (!res.ok) throw new Error(`Gagal memuat log audit (HTTP ${res.status})`);
  const body: unknown = await res.json();
  return z.array(AuditLogEntrySchema).parse(body);
}

export async function fetchRingkasanRegionalServer(): Promise<RingkasanFaskes[]> {
  const res = await serverFetch("/api/dinas-kesehatan/ringkasan");
  if (!res.ok) throw new Error(`Gagal memuat ringkasan regional (HTTP ${res.status})`);
  const body: unknown = await res.json();
  return z.array(RingkasanFaskesSchema).parse(body);
}

export async function fetchAiConfigServer(): Promise<AiConfig> {
  const res = await serverFetch("/api/superadmin/konfigurasi-ai");
  if (!res.ok) throw new Error(`Gagal memuat konfigurasi AI (HTTP ${res.status})`);
  const body: unknown = await res.json();
  return AiConfigSchema.parse(body);
}
