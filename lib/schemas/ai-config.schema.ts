import { z } from "zod";

/**
 * AiConfigSchema - ambang batas skor klasifikasi yang bisa diatur Super
 * Admin, dibaca langsung oleh lib/classify.ts. Sebelumnya nilai ini
 * hardcoded (skor >= 6 kritis, dst) — sekarang benar-benar bisa diubah
 * lewat halaman Konfigurasi Model AI, bukan cuma tampilan statis.
 */
export const AiConfigSchema = z.object({
  versiModel: z.string().min(1),
  ambangKritis: z.number().int().min(1).max(20),
  ambangTinggi: z.number().int().min(1).max(20),
  ambangSedang: z.number().int().min(1).max(20),
  wajibkanValidasiDpjUntukKritis: z.boolean(),
});
export type AiConfig = z.infer<typeof AiConfigSchema>;

export const UpdateAiConfigPayloadSchema = AiConfigSchema.refine(
  (v) => v.ambangKritis > v.ambangTinggi && v.ambangTinggi > v.ambangSedang,
  { message: "Ambang batas harus berurutan: Kritis > Tinggi > Sedang", path: ["ambangKritis"] },
);
