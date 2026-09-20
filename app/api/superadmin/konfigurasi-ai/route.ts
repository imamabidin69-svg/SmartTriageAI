import { NextResponse } from "next/server";
import { getAiConfig, setAiConfig } from "@/lib/data/ai-config-store";
import { UpdateAiConfigPayloadSchema } from "@/lib/schemas/ai-config.schema";
import { getSession } from "@/lib/session";

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
