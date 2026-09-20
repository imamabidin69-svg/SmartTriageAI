import { NextResponse } from "next/server";
import { classify } from "@/lib/classify";
import { insertTriase, listTriase } from "@/lib/data/triase-store";
import { assignPoliDanDokter } from "@/lib/poli-assignment";
import { TriageInputSchema, TriageRecordSchema } from "@/lib/schemas/triase.schema";
import { getSession } from "@/lib/session";

/** GET /api/triase - daftar antrean terurut prioritas kegawatan, dibatasi ke faskes pengguna. */
export async function GET() {
  const session = await getSession();
  if (!session) {
    return NextResponse.json({ error: "Sesi tidak ditemukan. Silakan masuk kembali." }, { status: 401 });
  }
  return NextResponse.json(listTriase(session.faskesId), { status: 200 });
}

/**
 * POST /api/triase - FR-03/04/05: submit gejala & tanda vital, server
 * menjalankan classify(). Sesuai tabel aktor SRS, hanya Perawat yang
 * berwenang di fungsi "Input gejala & tanda vital" — DPJ TIDAK berwenang
 * (wewenangnya ada di validasi/koreksi, bukan input awal).
 */
export async function POST(request: Request) {
  const session = await getSession();
  if (!session) {
    return NextResponse.json({ error: "Sesi tidak ditemukan. Silakan masuk kembali." }, { status: 401 });
  }
  if (session.role !== "perawat") {
    return NextResponse.json(
      { error: "Hanya Perawat yang berwenang menginput gejala & tanda vital pasien baru." },
      { status: 403 },
    );
  }

  const body: unknown = await request.json().catch(() => null);
  const parsed = TriageInputSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json({ error: "Data triase tidak valid.", issues: parsed.error.issues }, { status: 400 });
  }

  const { riskLevel, penjelasanAi } = classify(parsed.data);
  const { poliTujuan, dokterRujukan } = assignPoliDanDokter(parsed.data, riskLevel);
  const record = TriageRecordSchema.parse({
    ...parsed.data,
    idTriase: crypto.randomUUID(),
    riskLevel,
    penjelasanAi,
    statusValidasi: "menunggu",
    waktuTriase: new Date().toISOString(),
    poliTujuan,
    dokterRujukan,
    faskesId: session.faskesId,
    dibuatOlehUserId: session.userId,
    dibuatOlehNama: session.nama,
  });

  insertTriase(record);
  return NextResponse.json(record, { status: 201 });
}
