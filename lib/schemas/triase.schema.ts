import { z } from "zod";

/**
 * Skema Zod - Single Source of Truth
 * ---------------------------------------------------------------------------
 * Port dari proyek Modul 3-4. Setiap skema merepresentasikan satu baris pada
 * Kamus Data (SKPL Bab VI.a) atau struktur tabel PDM (SKPL Bab VI.c). Skema
 * yang sama kini dipakai di DUA sisi: Route Handler (server, validasi input
 * masuk) dan Client Component (validasi form sebelum submit) — end-to-end
 * type safety sesuai anjuran Modul 6 & 7.
 */

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

/**
 * Role yang "Terikat 1 Faskes" (lihat tabel aktor SRS) — hanya role inilah
 * yang boleh didaftarkan oleh Admin Faskes untuk stafnya sendiri.
 * super_admin/auditor/dinas_kesehatan bersifat lintas-faskes/eksternal,
 * jadi di luar wewenang provisioning Admin Faskes satu lokasi.
 */
export const FacilityBoundRoleSchema = z.enum(["perawat", "dokter_pj", "petugas_pendaftaran", "admin_faskes"]);
export type FacilityBoundRole = z.infer<typeof FacilityBoundRoleSchema>;

/**
 * VitalSignsSchema - HANYA menolak data yang mustahil secara fisik (negatif,
 * atau jauh di luar batas yang pernah tercatat dalam literatur medis).
 * Nilai yang tidak wajar secara klinis TAPI masih mungkin terjadi pada kasus
 * nyata (mis. suhu 41°C pada heatstroke berat) TIDAK ditolak di sini — itu
 * ditangani sebagai peringatan lunak (soft warning) di
 * lib/vital-warnings.ts + konfirmasi di TriaseFormClient, bukan pemblokiran
 * keras. Alasannya: menolak input sepenuhnya berisiko menghalangi
 * pendokumentasian kasus gawat darurat sungguhan yang justru paling butuh
 * dicatat segera.
 */
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
});
export type TriageInput = z.infer<typeof TriageInputSchema>;

export const RiskLevelSchema = z.enum(["rendah", "sedang", "tinggi", "kritis"]);
export type RiskLevel = z.infer<typeof RiskLevelSchema>;

export const StatusValidasiSchema = z.enum(["menunggu", "disetujui", "menunggu_review_dokter", "dikoreksi"]);
export type StatusValidasi = z.infer<typeof StatusValidasiSchema>;

export const JenisDokterSchema = z.enum(["umum", "spesialis"]);
export type JenisDokter = z.infer<typeof JenisDokterSchema>;

/**
 * DokterRujukanSchema - dokter yang MENANGANI pasien di poli tujuan.
 * Sengaja dinamai "dokterRujukan" (bukan "dokterPenanggungJawab") supaya
 * tidak rancu dengan role "dokter_pj" (DPJ) pada RBAC sistem — DPJ adalah
 * dokter yang memvalidasi/mengoreksi hasil AI (FR-06/07), sedangkan
 * dokterRujukan di sini adalah dokter poli yang akan merawat pasien
 * setelah triase selesai. Dua konsep berbeda yang kebetulan sama-sama
 * "dokter", jadi penamaan dipisah tegas untuk menghindari kebingungan.
 */
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

/**
 * ValidasiTriaseSchema - tiga aksi berbeda sesuai alur FR-06/07/08:
 * - "setujui" (FR-06): siapa pun tenaga medis, TAPI untuk risk level KRITIS
 *   hanya DPJ yang berwenang (ditegakkan di Route Handler, lihat
 *   app/api/triase/[id]/validasi/route.ts).
 * - "koreksi" (FR-07): KHUSUS DPJ, siapa pun kondisinya (mengubah angka
 *   risk level — wewenang klinis penuh).
 * - "ajukan_review" (FR-08): dipakai Perawat saat TIDAK sepakat dengan
 *   rekomendasi AI tapi TIDAK berwenang mengoreksi angka sendiri — status
 *   berubah jadi "menunggu_review_dokter", menunggu DPJ turun tangan.
 */
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

/** Payload login (FR-01) - email + password sungguhan, divalidasi di Route Handler /api/auth/login. */
export const LoginPayloadSchema = z.object({
  email: z.string().min(1, "Email wajib diisi").email("Format email tidak valid"),
  password: z.string().min(1, "Password wajib diisi"),
});
export type LoginPayload = z.infer<typeof LoginPayloadSchema>;

/** Payload lupa password - hanya email; alur pengiriman email sungguhan belum diimplementasikan (lihat lib/data/user-store.ts). */
export const ForgotPasswordPayloadSchema = z.object({
  email: z.string().min(1, "Email wajib diisi").email("Format email tidak valid"),
});
export type ForgotPasswordPayload = z.infer<typeof ForgotPasswordPayloadSchema>;

/**
 * Payload registrasi staf baru (FR-01 lanjutan) - HANYA bisa dipanggil oleh
 * sesi Admin Faskes yang sudah login (lihat app/api/admin/staff/route.ts).
 * faskesId TIDAK diminta dari form — selalu diambil dari sesi Admin Faskes
 * yang mendaftarkan, supaya satu admin tidak bisa mendaftarkan akun untuk
 * faskes lain (least privilege).
 */
export const RegisterStaffPayloadSchema = z.object({
  nama: z.string().min(2, "Nama wajib diisi (minimal 2 karakter)").max(120),
  email: z.string().min(1, "Email wajib diisi").email("Format email tidak valid"),
  password: z.string().min(8, "Password minimal 8 karakter"),
  role: FacilityBoundRoleSchema,
});
export type RegisterStaffPayload = z.infer<typeof RegisterStaffPayloadSchema>;

/**
 * Payload edit staf yang SUDAH ADA - Admin Faskes mengubah nama, email,
 * dan/atau peran akun nakes lain di faskesnya sendiri. Tidak termasuk
 * password (reset password punya alur terpisah lewat antrean permintaan
 * reset, lihat lib/data/password-reset-store.ts) dan tidak termasuk
 * isActive (punya endpoint/aksi toggle terpisah, lebih eksplisit).
 */
export const UpdateStaffPayloadSchema = z.object({
  nama: z.string().min(2, "Nama wajib diisi (minimal 2 karakter)").max(120),
  email: z.string().min(1, "Email wajib diisi").email("Format email tidak valid"),
  role: FacilityBoundRoleSchema,
});
export type UpdateStaffPayload = z.infer<typeof UpdateStaffPayloadSchema>;

/** Entitas Faskes (fasilitas kesehatan) - satu Admin Faskes & stafnya terikat pada satu faskesId. */
export const FaskesSchema = z.object({
  id: z.string().uuid(),
  nama: z.string(),
});
export type Faskes = z.infer<typeof FaskesSchema>;

/**
 * Entitas User (akun login sungguhan) - password TIDAK PERNAH dikirim ke
 * klien; passwordHash hanya hidup di server (lib/data/user-store.ts).
 * UserPublicSchema adalah bentuk yang aman ditampilkan di UI (tanpa hash).
 */
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

/**
 * Payload "Ubah Profil Akun" - tersedia untuk SEMUA role yang login (bukan
 * cuma Admin Faskes), karena mengubah nama/password akun sendiri adalah
 * kebutuhan dasar tiap pengguna. passwordSaatIni wajib diisi HANYA kalau
 * passwordBaru diisi (tidak bisa ganti password tanpa membuktikan tahu
 * password lama, walau sudah dalam sesi terautentikasi — pertahanan
 * berlapis terhadap sesi yang dibajak).
 */
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

/** Bentuk sesi yang disimpan di cookie httpOnly (dibaca middleware & Server Components). */
export const SessionSchema = z.object({
  userId: z.string().uuid(),
  nama: z.string(),
  role: RoleSchema,
  faskesId: z.string().uuid(),
  faskesNama: z.string(),
});
export type Session = z.infer<typeof SessionSchema>;
