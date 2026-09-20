import { NextResponse } from "next/server";
import { listTriase } from "@/lib/data/triase-store";
import { getSession } from "@/lib/session";

/** GET /api/triase/riwayat?nama=... - seluruh riwayat triase pasien dengan nama yang cocok (Perawat & DPJ). */
export async function GET(request: Request) {
  const session = await getSession();
  if (!session) {
    return NextResponse.json({ error: "Sesi tidak ditemukan. Silakan masuk kembali." }, { status: 401 });
  }
  if (session.role !== "perawat" && session.role !== "dokter_pj") {
    return NextResponse.json({ error: "Anda tidak berwenang melihat riwayat triase." }, { status: 403 });
  }

  const url = new URL(request.url);
  const nama = url.searchParams.get("nama")?.trim().toLowerCase() ?? "";
  if (!nama) {
    return NextResponse.json([], { status: 200 });
  }

  const hasil = listTriase(session.faskesId).filter((r) => r.namaPasien.toLowerCase().includes(nama));
  return NextResponse.json(hasil, { status: 200 });
}
