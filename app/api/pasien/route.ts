import { NextResponse } from "next/server";
import { appendAuditLog } from "@/lib/data/audit-store";
import { insertPasien, listPasienByFaskes } from "@/lib/data/pasien-store";
import { PasienSchema, RegisterPasienPayloadSchema } from "@/lib/schemas/pasien.schema";
import { getSession } from "@/lib/session";

/** GET /api/pasien - daftar pasien terdaftar di faskes pengguna yang login (Petugas Pendaftaran, Perawat, DPJ). */
export async function GET() {
  const session = await getSession();
  if (!session) {
    return NextResponse.json({ error: "Sesi tidak ditemukan. Silakan masuk kembali." }, { status: 401 });
  }
  return NextResponse.json(listPasienByFaskes(session.faskesId), { status: 200 });
}

/**
 * POST /api/pasien - registrasi pasien baru. Sesuai tabel aktor SRS,
 * Petugas Pendaftaran adalah jalur normal untuk fungsi ini; Perawat tetap
 * diizinkan (jalur darurat untuk pasien tidak sadar tanpa pendamping saat
 * petugas belum sempat menjangkau) — lihat catatan desain terkait role ini.
 */
export async function POST(request: Request) {
  const session = await getSession();
  if (!session) {
    return NextResponse.json({ error: "Sesi tidak ditemukan. Silakan masuk kembali." }, { status: 401 });
  }
  if (session.role !== "petugas_pendaftaran" && session.role !== "perawat") {
    return NextResponse.json({ error: "Anda tidak berwenang meregistrasi pasien baru." }, { status: 403 });
  }

  const body: unknown = await request.json().catch(() => null);
  const parsed = RegisterPasienPayloadSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json({ error: "Data pasien tidak valid.", issues: parsed.error.issues }, { status: 400 });
  }

  const pasien = PasienSchema.parse({
    id: crypto.randomUUID(),
    ...parsed.data,
    faskesId: session.faskesId,
    didaftarkanOlehUserId: session.userId,
    didaftarkanOlehNama: session.nama,
    waktuDaftar: new Date().toISOString(),
  });

  insertPasien(pasien);

  appendAuditLog({
    id: crypto.randomUUID(),
    faskesId: session.faskesId,
    faskesNama: session.faskesNama,
    aksi: "pasien_didaftarkan",
    aktorUserId: session.userId,
    aktorNama: session.nama,
    targetNama: pasien.nama,
    waktu: new Date().toISOString(),
  });

  return NextResponse.json(pasien, { status: 201 });
}
