import { NextResponse } from "next/server";
import { listAllAuditLog } from "@/lib/data/audit-store";
import { getSession } from "@/lib/session";

export async function GET() {
  const session = await getSession();
  if (!session) {
    return NextResponse.json({ error: "Sesi tidak ditemukan. Silakan masuk kembali." }, { status: 401 });
  }
  if (session.role !== "auditor") {
    return NextResponse.json({ error: "Hanya Auditor yang berwenang mengakses log ini." }, { status: 403 });
  }

  return NextResponse.json(listAllAuditLog(), { status: 200 });
}
