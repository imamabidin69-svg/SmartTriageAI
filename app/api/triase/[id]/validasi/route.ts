import { NextResponse } from "next/server";
import { appendAuditLog } from "@/lib/data/audit-store";
import { getTriaseById, updateTriase } from "@/lib/data/triase-store";
import { ValidasiTriaseSchema } from "@/lib/schemas/triase.schema";
import { canOverride, getSession } from "@/lib/session";

/**
 * PATCH /api/triase/[id]/validasi - Setujui, Koreksi (khusus DPJ), atau
 * Ajukan Review Dokter. Seluruh wewenang ditegakkan DI SERVER (bukan hanya
 * disembunyikan di UI klien), karena tombol yang disembunyikan tetap bisa
 * dilewati dengan memanggil API langsung.
 *
 * Aturan wewenang:
 * - "setujui" pada kasus risk level KRITIS: hanya DPJ.
 * - "setujui" pada kasus non-kritis: siapa pun tenaga medis yang login.
 * - "koreksi": khusus DPJ, tanpa syarat risk level.
 * - "ajukan_review": tersedia untuk non-DPJ yang tidak sepakat dengan
 *   rekomendasi AI tapi tidak berwenang mengoreksi angka sendiri.
 *
 * Setiap aksi juga dicatat ke log audit (lib/data/audit-store.ts) untuk
 * peran Auditor.
 */
export async function PATCH(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const session = await getSession();
  if (!session) {
    return NextResponse.json({ error: "Sesi tidak ditemukan. Silakan masuk kembali." }, { status: 401 });
  }

  const { id } = await params;
  const body: unknown = await request.json().catch(() => null);
  const parsed = ValidasiTriaseSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json({ error: "Payload validasi tidak valid.", issues: parsed.error.issues }, { status: 400 });
  }
  if (parsed.data.idTriase !== id) {
    return NextResponse.json({ error: "ID triase pada URL dan payload tidak cocok." }, { status: 400 });
  }

  const existing = getTriaseById(id);
  if (!existing) {
    return NextResponse.json({ error: "Data triase tidak ditemukan." }, { status: 404 });
  }

  const payload = parsed.data;

  if (payload.aksi === "koreksi" && !canOverride(session)) {
    return NextResponse.json(
      { error: "Hanya Dokter Penanggung Jawab (DPJ) yang berwenang mengoreksi risk level." },
      { status: 403 },
    );
  }
  if (payload.aksi === "setujui" && existing.riskLevel === "kritis" && !canOverride(session)) {
    return NextResponse.json(
      {
        error:
          "Kasus dengan risk level KRITIS wajib ditangani Dokter Penanggung Jawab (DPJ) — Anda tidak berwenang menyetujui sendiri.",
      },
      { status: 403 },
    );
  }

  const riskLevelSebelum = existing.riskLevel;

  const updated = updateTriase(id, (current) => {
    if (payload.aksi === "setujui") {
      return {
        ...current,
        statusValidasi: "disetujui",
        divalidasiOlehUserId: session.userId,
        divalidasiOlehNama: session.nama,
      };
    }
    if (payload.aksi === "koreksi") {
      return {
        ...current,
        riskLevel: payload.riskLevelBaru,
        statusValidasi: "dikoreksi",
        penjelasanAi: `${current.penjelasanAi} [Dikoreksi oleh DPJ: ${payload.catatanKoreksi}]`,
        divalidasiOlehUserId: session.userId,
        divalidasiOlehNama: session.nama,
      };
    }
    // aksi === "ajukan_review"
    return {
      ...current,
      statusValidasi: "menunggu_review_dokter",
      penjelasanAi: `${current.penjelasanAi} [Perawat mengajukan review dokter: ${payload.catatanPerawat}]`,
    };
  });

  if (!updated) {
    return NextResponse.json({ error: "Data triase tidak ditemukan." }, { status: 404 });
  }

  appendAuditLog({
    id: crypto.randomUUID(),
    idTriase: id,
    targetNama: updated.namaPasien,
    faskesId: session.faskesId,
    faskesNama: session.faskesNama,
    aksi: payload.aksi,
    aktorUserId: session.userId,
    aktorNama: session.nama,
    riskLevelSebelum,
    riskLevelSesudah: updated.riskLevel,
    catatan:
      payload.aksi === "koreksi"
        ? payload.catatanKoreksi
        : payload.aksi === "ajukan_review"
          ? payload.catatanPerawat
          : undefined,
    waktu: new Date().toISOString(),
  });

  return NextResponse.json(updated, { status: 200 });
}
