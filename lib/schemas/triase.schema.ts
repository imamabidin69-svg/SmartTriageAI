import { z } from "zod";

export const RoleSchema = z.enum([
  "perawat",
  "dokter_pj",
  "petugas_pendaftaran",
  "admin_faskes",
  "super_admin",
  "auditor",
  "dinas_kesehatan",
]);
export type Role = z.infer<typeof RoleSchema>;

export const FacilityBoundRoleSchema = z.enum(["perawat", "dokter_pj", "petugas_pendaftaran", "admin_faskes"]);
export type FacilityBoundRole = z.infer<typeof FacilityBoundRoleSchema>;

export const VitalSignsSchema = z.object({
  tekananDarahSistolik: z
    .number({ invalid_type_error: "Tekanan darah sistolik wajib berupa angka" })
    .int()
    .min(0, "Tekanan darah sistolik tidak boleh negatif")
    .max(320, "Nilai tekanan darah sistolik di luar batas yang bisa dicatat sistem"),
  tekananDarahDiastolik: z
    .number({ invalid_type_error: "Tekanan darah diastolik wajib berupa angka" })
    .int()
    .min(0, "Tekanan darah diastolik tidak boleh negatif")
    .max(200, "Nilai tekanan darah diastolik di luar batas yang bisa dicatat sistem"),
  suhuTubuh: z
    .number({ invalid_type_error: "Suhu tubuh wajib berupa angka" })
    .min(20, "Nilai suhu tubuh di luar batas yang bisa dicatat sistem")
    .max(45, "Nilai suhu tubuh di luar batas yang bisa dicatat sistem"),
  nadiPerMenit: z
    .number({ invalid_type_error: "Nadi wajib berupa angka" })
    .int()
    .min(0, "Nadi tidak boleh negatif")
    .max(300, "Nilai nadi di luar batas yang bisa dicatat sistem"),
  lajuNapas: z
    .number({ invalid_type_error: "Laju napas wajib berupa angka" })
    .int()
    .min(0, "Laju napas tidak boleh negatif")
    .max(80, "Nilai laju napas di luar batas yang bisa dicatat sistem"),
  saturasiOksigen: z
    .number({ invalid_type_error: "Saturasi oksigen wajib berupa angka" })
    .min(0, "Saturasi oksigen minimal 0%")
    .max(100, "Saturasi oksigen maksimal 100%"),
});
export type VitalSigns = z.infer<typeof VitalSignsSchema>;

// Kategori keluhan untuk model machine learning (lib/ml-client.ts). Daftar ini
// SAMA PERSIS dengan kategori yang dipakai saat melatih model (lihat
// triase_data.py, ATURAN_KELUHAN) supaya nilainya bisa diteruskan langsung ke
// layanan ML tanpa tabel pemetaan tambahan.
export const KategoriKeluhanSchema = z.enum([
  "Penurunan kesadaran atau kejang",
  "Nyeri dada",
  "Sesak napas atau batuk",
  "Perdarahan",
  "Gangguan saraf",
  "Nyeri perut",
  "Demam",
  "Pusing",
  "Nyeri kepala",
  "Mual, muntah, atau diare",
  "Cedera atau luka",
  "Jantung berdebar",
  "Kulit atau alergi",
  "Mata, telinga, hidung, atau tenggorokan",
  "Nyeri punggung, pinggang, atau anggota gerak",
  "Lemas atau kelemahan umum",
  "Keluhan kemih atau kandungan",
  "Lainnya",
]);
export type KategoriKeluhan = z.infer<typeof KategoriKeluhanSchema>;

// Skala AVPU. Urutan dari paling sadar ke paling tidak sadar (dipetakan ke
// kode 1-4 di lib/ml-client.ts sebelum dikirim ke layanan ML).
export const TingkatKesadaranSchema = z.enum(["sadar_penuh", "respons_suara", "respons_nyeri", "tidak_respons"]);
export type TingkatKesadaran = z.infer<typeof TingkatKesadaranSchema>;

export const TriageInputSchema = z.object({
  idPasien: z.string().uuid("ID pasien tidak valid"),
  namaPasien: z.string().min(1, "Nama pasien wajib diisi").max(120),
  gejala: z
    .string()
    .min(10, "Uraian gejala minimal 10 karakter agar AI dapat menganalisis dengan baik")
    .max(2000, "Uraian gejala maksimal 2000 karakter"),
  keluhanUtama: z.string().min(3, "Keluhan utama wajib diisi").max(200),
  riwayatSingkat: z.string().max(1000, "Riwayat singkat maksimal 1000 karakter").optional(),
  tandaVital: VitalSignsSchema,
  // Isian baru untuk model machine learning (menggantikan classify.ts berbasis
  // aturan). Opsional supaya form lama yang belum diperbarui tetap valid;
  // lib/ml-client.ts memakai imputasi median/modus kalau kosong, sama seperti
  // yang sudah diuji di notebooks/02_baseline.ipynb.
  skalaNyeri: z.number().min(0, "Skala nyeri minimal 0").max(10, "Skala nyeri maksimal 10").optional(),
  tingkatKesadaran: TingkatKesadaranSchema.optional(),
  kategoriKeluhan: KategoriKeluhanSchema.optional(),
});
export type TriageInput = z.infer<typeof TriageInputSchema>;

export const RiskLevelSchema = z.enum(["rendah", "sedang", "tinggi", "kritis"]);
export type RiskLevel = z.infer<typeof RiskLevelSchema>;

export const StatusValidasiSchema = z.enum(["menunggu", "disetujui", "menunggu_review_dokter", "dikoreksi"]);
export type StatusValidasi = z.infer<typeof StatusValidasiSchema>;

export const JenisDokterSchema = z.enum(["umum", "spesialis"]);
export type JenisDokter = z.infer<typeof JenisDokterSchema>;

export const DokterRujukanSchema = z.object({
  nama: z.string(),
  jenis: JenisDokterSchema,
  spesialisasi: z.string().optional(),
});
export type DokterRujukan = z.infer<typeof DokterRujukanSchema>;

export const TriageResultSchema = z.object({
  idTriase: z.string().uuid(),
  riskLevel: RiskLevelSchema,
  penjelasanAi: z.string().min(1, "Penjelasan AI tidak boleh kosong"),
  statusValidasi: StatusValidasiSchema,
  waktuTriase: z.string().datetime({ message: "Format waktu tidak valid (ISO 8601)" }),
  poliTujuan: z.string().min(1, "Poli tujuan wajib ditentukan"),
  dokterRujukan: DokterRujukanSchema,
  faskesId: z.string().uuid(),
  dibuatOlehUserId: z.string().uuid(),
  dibuatOlehNama: z.string(),
  divalidasiOlehUserId: z.string().uuid().optional(),
  divalidasiOlehNama: z.string().optional(),
});
export type TriageResult = z.infer<typeof TriageResultSchema>;

export const TriageRecordSchema = TriageInputSchema.merge(TriageResultSchema);
export type TriageRecord = z.infer<typeof TriageRecordSchema>;

export const ValidasiTriaseSchema = z.discriminatedUnion("aksi", [
  z.object({
    aksi: z.literal("setujui"),
    idTriase: z.string().uuid(),
    idUserValidator: z.string().uuid(),
  }),
  z.object({
    aksi: z.literal("koreksi"),
    idTriase: z.string().uuid(),
    idUserValidator: z.string().uuid(),
    riskLevelBaru: RiskLevelSchema,
    catatanKoreksi: z.string().min(5, "Catatan koreksi wajib diisi minimal 5 karakter (akuntabilitas NFR-10)"),
  }),
  z.object({
    aksi: z.literal("ajukan_review"),
    idTriase: z.string().uuid(),
    idUserValidator: z.string().uuid(),
    catatanPerawat: z.string().min(5, "Catatan wajib diisi minimal 5 karakter — jelaskan alasan tidak sepakat"),
  }),
]);
export type ValidasiTriase = z.infer<typeof ValidasiTriaseSchema>;

export const LoginPayloadSchema = z.object({
  email: z.string().min(1, "Email wajib diisi").email("Format email tidak valid"),
  password: z.string().min(1, "Password wajib diisi"),
});
export type LoginPayload = z.infer<typeof LoginPayloadSchema>;

export const ForgotPasswordPayloadSchema = z.object({
  email: z.string().min(1, "Email wajib diisi").email("Format email tidak valid"),
});
export type ForgotPasswordPayload = z.infer<typeof ForgotPasswordPayloadSchema>;

export const RegisterStaffPayloadSchema = z.object({
  nama: z.string().min(2, "Nama wajib diisi (minimal 2 karakter)").max(120),
  email: z.string().min(1, "Email wajib diisi").email("Format email tidak valid"),
  password: z.string().min(8, "Password minimal 8 karakter"),
  role: FacilityBoundRoleSchema,
});
export type RegisterStaffPayload = z.infer<typeof RegisterStaffPayloadSchema>;

export const UpdateStaffPayloadSchema = z.object({
  nama: z.string().min(2, "Nama wajib diisi (minimal 2 karakter)").max(120),
  email: z.string().min(1, "Email wajib diisi").email("Format email tidak valid"),
  role: FacilityBoundRoleSchema,
});
export type UpdateStaffPayload = z.infer<typeof UpdateStaffPayloadSchema>;

export const FaskesSchema = z.object({
  id: z.string().uuid(),
  nama: z.string(),
});
export type Faskes = z.infer<typeof FaskesSchema>;

export const UserSchema = z.object({
  id: z.string().uuid(),
  nama: z.string(),
  email: z.string().email(),
  passwordHash: z.string(),
  role: RoleSchema,
  faskesId: z.string().uuid(),
  isActive: z.boolean(),
  createdAt: z.string().datetime(),
});
export type User = z.infer<typeof UserSchema>;

export const RingkasanFaskesSchema = z.object({
  faskesId: z.string().uuid(),
  faskesNama: z.string(),
  totalTriase: z.number().int(),
  perLevel: z.record(z.string(), z.number().int()),
});
export type RingkasanFaskes = z.infer<typeof RingkasanFaskesSchema>;

export const FaskesRingkasanSchema = z.object({
  id: z.string().uuid(),
  nama: z.string(),
  jumlahStaf: z.number().int(),
  jumlahTriase: z.number().int(),
});
export type FaskesRingkasan = z.infer<typeof FaskesRingkasanSchema>;

export const UserPublicSchema = UserSchema.omit({ passwordHash: true });
export type UserPublic = z.infer<typeof UserPublicSchema>;

export const UpdateProfilePayloadSchema = z
  .object({
    nama: z.string().min(2, "Nama wajib diisi (minimal 2 karakter)").max(120),
    passwordSaatIni: z.string().optional(),
    passwordBaru: z.string().min(8, "Password baru minimal 8 karakter").optional(),
  })
  .refine((data) => !data.passwordBaru || (data.passwordSaatIni && data.passwordSaatIni.length > 0), {
    message: "Password saat ini wajib diisi untuk mengganti password",
    path: ["passwordSaatIni"],
  });
export type UpdateProfilePayload = z.infer<typeof UpdateProfilePayloadSchema>;

export const SessionSchema = z.object({
  userId: z.string().uuid(),
  nama: z.string(),
  role: RoleSchema,
  faskesId: z.string().uuid(),
  faskesNama: z.string(),
});
export type Session = z.infer<typeof SessionSchema>;
