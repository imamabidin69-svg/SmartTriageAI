import { z } from "zod";

export const JenisKelaminSchema = z.enum(["laki_laki", "perempuan"]);
export type JenisKelamin = z.infer<typeof JenisKelaminSchema>;

export const PasienSchema = z.object({
  id: z.string().uuid(),
  nama: z.string().min(1),
  nik: z.string().length(16).optional(),
  tanggalLahir: z.string().optional(),
  jenisKelamin: JenisKelaminSchema.optional(),
  alamat: z.string().optional(),
  noTelepon: z.string().optional(),
  faskesId: z.string().uuid(),
  didaftarkanOlehUserId: z.string().uuid(),
  didaftarkanOlehNama: z.string(),
  waktuDaftar: z.string().datetime(),
});
export type Pasien = z.infer<typeof PasienSchema>;

export const RegisterPasienPayloadSchema = z.object({
  nama: z.string().min(2, "Nama wajib diisi (minimal 2 karakter)").max(120),
  nik: z
    .string()
    .length(16, "NIK harus 16 digit")
    .optional()
    .or(z.literal("").transform(() => undefined)),
  tanggalLahir: z.string().optional(),
  jenisKelamin: JenisKelaminSchema.optional(),
  alamat: z.string().max(300).optional(),
  noTelepon: z.string().max(20).optional(),
});
export type RegisterPasienPayload = z.infer<typeof RegisterPasienPayloadSchema>;
