import { NextResponse } from "next/server";
import { listPendingByFaskes } from "@/lib/data/password-reset-store";
import { getSession } from "@/lib/session";

export async function GET() {
  const session = await getSession();
  if (!session) {
    return NextResponse.json({ error: "Sesi tidak ditemukan. Silakan masuk kembali." }, { status: 401 });
  }
  if (session.role !== "admin_faskes") {
    return NextResponse.json({ error: "Hanya Admin Faskes yang berwenang melihat permintaan ini." }, { status: 403 });
  }

  return NextResponse.json(listPendingByFaskes(session.faskesId), { status: 200 });
}
