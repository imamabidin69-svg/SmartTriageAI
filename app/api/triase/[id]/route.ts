import { NextResponse } from "next/server";
import { getTriaseById } from "@/lib/data/triase-store";
import { getSession } from "@/lib/session";

/** GET /api/triase/[id] - detail satu hasil triase (Hasil & Penjelasan AI). */
export async function GET(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const session = await getSession();
  if (!session) {
    return NextResponse.json({ error: "Sesi tidak ditemukan. Silakan masuk kembali." }, { status: 401 });
  }

  const { id } = await params;
  const record = getTriaseById(id);
  if (!record) {
    return NextResponse.json({ error: "Data triase tidak ditemukan." }, { status: 404 });
  }
  return NextResponse.json(record, { status: 200 });
}
