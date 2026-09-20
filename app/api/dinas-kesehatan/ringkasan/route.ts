import { NextResponse } from "next/server";
import { listTriaseAllFaskes } from "@/lib/data/triase-store";
import { listAllFaskes } from "@/lib/data/user-store";
import { getSession } from "@/lib/session";

/** GET /api/dinas-kesehatan/ringkasan - agregat statistik triase lintas-faskes (read-only, eksternal). */
export async function GET() {
  const session = await getSession();
  if (!session) {
    return NextResponse.json({ error: "Sesi tidak ditemukan. Silakan masuk kembali." }, { status: 401 });
  }
  if (session.role !== "dinas_kesehatan") {
    return NextResponse.json({ error: "Hanya Dinas Kesehatan yang berwenang mengakses data ini." }, { status: 403 });
  }

  const faskesList = listAllFaskes().filter((f) => f.id !== "c0000000-0000-4000-8000-000000000099");
  const allTriase = listTriaseAllFaskes();

  const perFaskes = faskesList.map((f) => {
    const records = allTriase.filter((r) => r.faskesId === f.id);
    const perLevel: Record<string, number> = { kritis: 0, tinggi: 0, sedang: 0, rendah: 0 };
    for (const r of records) perLevel[r.riskLevel] = (perLevel[r.riskLevel] ?? 0) + 1;
    return { faskesId: f.id, faskesNama: f.nama, totalTriase: records.length, perLevel };
  });

  return NextResponse.json(perFaskes, { status: 200 });
}
