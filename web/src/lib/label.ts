import type { AksiAudit, Peran, RiskLevel } from "@/api/tipe";

export const LABEL_PERAN: Record<Peran, string> = {
  perawat: "Perawat",
  dokter: "Dokter",
  admin: "Admin",
};

export const LABEL_LEVEL: Record<RiskLevel, string> = {
  rendah: "Rendah",
  sedang: "Sedang",
  tinggi: "Tinggi",
  kritis: "Kritis",
};

export const URUTAN_LEVEL: RiskLevel[] = ["kritis", "tinggi", "sedang", "rendah"];

export const LABEL_AKSI: Record<AksiAudit, string> = {
  setujui: "Menyetujui triase",
  koreksi: "Mengoreksi risk level",
  ajukan_review: "Mengajukan review",
  ubah_konfigurasi: "Mengubah pengaturan",
  tambah_staf: "Menambah staf",
  ubah_staf: "Mengubah data staf",
  nonaktifkan_staf: "Menonaktifkan staf",
  aktifkan_staf: "Mengaktifkan staf",
  atur_ulang_password: "Mengatur ulang password",
  registrasi_kunjungan: "Registrasi kunjungan",
};
