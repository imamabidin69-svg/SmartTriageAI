/** Nama pendek untuk tipe yang dibangkitkan dari spesifikasi OpenAPI backend (npm run api:tipe). */
import type { components } from "./skema";

type Skema = components["schemas"];

export type Peran = Skema["Peran"];
export type RiskLevel = Skema["RiskLevel"];
export type AksiAudit = Skema["AksiAudit"];
export type Pengguna = Skema["PenggunaResponse"];
export type SesiLogin = Skema["SesiResponse"];
export type Staf = Skema["StafResponse"];
export type StafDisimpan = Skema["StafDisimpanResponse"];
export type StafBaru = Skema["StafRequest"];
export type StafPatch = Skema["StafPatch"];
export type Konfigurasi = Skema["KonfigurasiResponse"];
export type KonfigurasiPatch = Skema["KonfigurasiPatch"];
export type Rekap = Skema["RekapResponse"];
export type ItemLogAudit = Skema["ItemLogAudit"];
export type HalamanLogAudit = Skema["LogAuditResponse"];
export type Health = Skema["HealthResponse"];
export type PengisiEir = Skema["PengisiEir"];
export type StatusSesiEir = Skema["StatusSesiEir"];
export type SesiEirDibuat = Skema["SesiEirDibuatResponse"];
export type BalasanEir = Skema["BalasanEirResponse"];
