import { NextResponse } from "next/server";
import { getAiConfig, setAiConfig } from "@/lib/data/ai-config-store";
import { UpdateAiConfigPayloadSchema } from "@/lib/schemas/ai-config.schema";
import { getSession } from "@/lib/session";

/** GET /api/superadmin/konfigurasi-ai - konfigurasi model AI saat ini (lintas-faskes). */
export async function GET() {
  const session = await getSession();
  if (!session) {
    return NextResponse.json({ error: "Sesi tidak ditemukan. Silakan masuk kembali." }, { status: 401 });
  }
  if (session.role !== "super_admin") {
    return NextResponse.json({ error: "Hanya Super Admin yang berwenang mengakses ini." }, { status: 403 });
  }
  return NextResponse.json(getAiConfig(), { status: 200 });
}

/**
 * PATCH /api/superadmin/konfigurasi-ai - ubah ambang batas & versi model.
 * Perubahan di sini LANGSUNG memengaruhi lib/classify.ts pada submit
 * triase berikutnya (bukan cuma tampilan) — lihat getAiConfig() yang
 * dipanggil classify() setiap kali dijalankan.
 */
export async function PATCH(request: Request) {
  const session = await getSession();
  if (!session) {
    return NextResponse.json({ error: "Sesi tidak ditemukan. Silakan masuk kembali." }, { status: 401 });
  }
  if (session.role !== "super_admin") {
    return NextResponse.json({ error: "Hanya Super Admin yang berwenang mengubah ini." }, { status: 403 });
  }

  const body: unknown = await request.json().catch(() => null);
  const parsed = UpdateAiConfigPayloadSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { error: parsed.error.issues[0]?.message ?? "Konfigurasi tidak valid.", issues: parsed.error.issues },
      { status: 400 },
    );
  }

  const updated = setAiConfig(parsed.data);
  return NextResponse.json(updated, { status: 200 });
}
