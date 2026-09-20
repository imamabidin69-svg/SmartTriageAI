import { NextResponse } from "next/server";
import { appendAuditLog } from "@/lib/data/audit-store";
import { insertPasien, listPasienByFaskes } from "@/lib/data/pasien-store";
import { PasienSchema, RegisterPasienPayloadSchema } from "@/lib/schemas/pasien.schema";
import { getSession } from "@/lib/session";

export async function GET() {
  const session = await getSession();
  if (!session) {
    return NextResponse.json({ error: "Sesi tidak ditemukan. Silakan masuk kembali." }, { status: 401 });
  }
  return NextResponse.json(listPasienByFaskes(session.faskesId), { status: 200 });
}

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
