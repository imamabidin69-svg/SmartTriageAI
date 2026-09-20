import { NextResponse } from "next/server";
import { listTriaseAllFaskes } from "@/lib/data/triase-store";
import { listAllFaskes, listAllUsers } from "@/lib/data/user-store";
import { getSession } from "@/lib/session";

/** GET /api/superadmin/faskes - seluruh faskes lintas-sistem beserta ringkasan jumlah staf & triase. Khusus Super Admin. */
export async function GET() {
  const session = await getSession();
  if (!session) {
    return NextResponse.json({ error: "Sesi tidak ditemukan. Silakan masuk kembali." }, { status: 401 });
  }
  if (session.role !== "super_admin") {
    return NextResponse.json({ error: "Hanya Super Admin yang berwenang mengakses data ini." }, { status: 403 });
  }

  const faskesList = listAllFaskes();
  const allUsers = listAllUsers();
  const allTriase = listTriaseAllFaskes();

  const ringkasan = faskesList.map((f) => ({
    id: f.id,
    nama: f.nama,
    jumlahStaf: allUsers.filter((u) => u.faskesId === f.id).length,
    jumlahTriase: allTriase.filter((r) => r.faskesId === f.id).length,
  }));

  return NextResponse.json(ringkasan, { status: 200 });
}
