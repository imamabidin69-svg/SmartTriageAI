/**
 * Klien HTTP untuk API Flask (/api/v1).
 *
 * Web admin memakai cookie HttpOnly dari login, jadi setiap request yang mengubah data wajib membawa header
 * X-CSRF-TOKEN yang dibaca dari cookie csrf_* (Desain 7.1). Access token berumur 15 menit; bila habis, klien
 * memanggil /auth/refresh sekali lalu mengulang request. Semua error server berformat Problem Details.
 *
 * Cookie access token berumur sama dengan tokennya, jadi saat token habis peramban biasanya sudah membuang
 * cookie-nya dan server menjawab "belum masuk", bukan "token kedaluwarsa". Karena itu refresh juga dicoba untuk
 * jawaban "belum masuk" selama cookie csrf_refresh_token (berumur 8 jam, sama dengan refresh token) masih ada.
 */

export const PREFIKS_API = "/api/v1";

export const TIPE = {
  VALIDASI: "urn:smarttriage:problem:validasi",
  TOKEN_KEDALUWARSA: "urn:smarttriage:problem:token-kedaluwarsa",
  TIDAK_TERAUTENTIKASI: "urn:smarttriage:problem:tidak-terautentikasi",
  TIDAK_TERHUBUNG: "urn:smarttriage:problem:tidak-terhubung",
} as const;

export interface FieldError {
  field: string;
  pesan: string;
}

export class ProblemError extends Error {
  readonly status: number;
  readonly tipe: string;
  readonly judul: string;
  readonly detail?: string;
  readonly errors: FieldError[];
  readonly isi: Record<string, unknown>;
  readonly cobaLagiDetik?: number;

  constructor(status: number, isi: Record<string, unknown>, cobaLagiDetik?: number) {
    const judul = typeof isi.title === "string" ? isi.title : "Terjadi kesalahan";
    const detail = typeof isi.detail === "string" ? isi.detail : undefined;
    super(detail ?? judul);
    this.name = "ProblemError";
    this.status = status;
    this.tipe = typeof isi.type === "string" ? isi.type : "about:blank";
    this.judul = judul;
    this.detail = detail;
    this.errors = Array.isArray(isi.errors) ? (isi.errors as FieldError[]) : [];
    this.isi = isi;
    this.cobaLagiDetik = cobaLagiDetik;
  }

  /** Pesan per field dalam bentuk { nama_field: pesan } untuk ditampilkan di bawah isian. */
  get pesanField(): Record<string, string> {
    return Object.fromEntries(this.errors.map((e) => [e.field, e.pesan]));
  }
}

export function pesanError(galat: unknown): string {
  if (galat instanceof ProblemError) return galat.detail ?? galat.judul;
  return "Terjadi kesalahan. Coba lagi beberapa saat lagi.";
}

export function bacaCookie(nama: string): string | undefined {
  for (const bagian of document.cookie.split(";")) {
    const [kunci, ...nilai] = bagian.trim().split("=");
    if (kunci === nama) return decodeURIComponent(nilai.join("="));
  }
  return undefined;
}

type NilaiQuery = string | number | boolean | null | undefined;

export interface OpsiPermintaan {
  method?: "GET" | "POST" | "PATCH";
  json?: unknown;
  form?: FormData;
  query?: Record<string, NilaiQuery>;
  /** Cookie CSRF yang dipakai: refresh untuk /auth/refresh dan /auth/logout. */
  csrf?: "access" | "refresh";
  header?: Record<string, string>;
  /** false supaya request tidak mencoba refresh token lagi (dipakai saat mengulang). */
  bolehRefresh?: boolean;
}

export function susunAlamat(path: string, query?: Record<string, NilaiQuery>): string {
  const params = new URLSearchParams();
  for (const [kunci, nilai] of Object.entries(query ?? {})) {
    if (nilai !== undefined && nilai !== null && nilai !== "") params.set(kunci, String(nilai));
  }
  const teks = params.toString();
  return `${PREFIKS_API}${path}${teks ? `?${teks}` : ""}`;
}

async function kirim(path: string, opsi: OpsiPermintaan): Promise<Response> {
  const method = opsi.method ?? "GET";
  const header: Record<string, string> = { Accept: "application/json", ...opsi.header };
  let body: BodyInit | undefined;
  if (opsi.json !== undefined) {
    header["Content-Type"] = "application/json";
    body = JSON.stringify(opsi.json);
  } else if (opsi.form) {
    body = opsi.form;
  }
  if (method !== "GET") {
    const csrf = bacaCookie(opsi.csrf === "refresh" ? "csrf_refresh_token" : "csrf_access_token");
    if (csrf) header["X-CSRF-TOKEN"] = csrf;
  }
  try {
    return await fetch(susunAlamat(path, opsi.query), { method, headers: header, body, credentials: "same-origin" });
  } catch {
    throw new ProblemError(0, {
      type: TIPE.TIDAK_TERHUBUNG,
      title: "Tidak dapat terhubung",
      detail: "Server tidak dapat dihubungi. Periksa koneksi internet lalu coba lagi.",
    });
  }
}

async function bacaGalat(respons: Response): Promise<ProblemError> {
  let isi: Record<string, unknown> = {};
  try {
    isi = (await respons.json()) as Record<string, unknown>;
  } catch {
    isi = { title: "Terjadi kesalahan pada server" };
  }
  const cobaLagi = Number(respons.headers.get("Retry-After"));
  return new ProblemError(respons.status, isi, Number.isFinite(cobaLagi) && cobaLagi > 0 ? cobaLagi : undefined);
}

let refreshBerjalan: Promise<boolean> | null = null;

/** Memperbarui access token lewat cookie refresh. Beberapa request yang gagal bersamaan hanya memicu satu refresh. */
export function perbaruiToken(): Promise<boolean> {
  refreshBerjalan ??= kirim("/auth/refresh", { method: "POST", csrf: "refresh" })
    .then((respons) => respons.ok)
    .catch(() => false)
    .finally(() => {
      refreshBerjalan = null;
    });
  return refreshBerjalan;
}

function perluRefresh(galat: ProblemError): boolean {
  if (galat.tipe === TIPE.TOKEN_KEDALUWARSA) return true;
  return galat.tipe === TIPE.TIDAK_TERAUTENTIKASI && bacaCookie("csrf_refresh_token") !== undefined;
}

async function responsBerhasil(path: string, opsi: OpsiPermintaan): Promise<Response> {
  const respons = await kirim(path, opsi);
  if (respons.ok) return respons;
  const galat = await bacaGalat(respons);
  if (galat.status === 401 && opsi.bolehRefresh !== false && perluRefresh(galat)) {
    if (await perbaruiToken()) return responsBerhasil(path, { ...opsi, bolehRefresh: false });
  }
  throw galat;
}

export async function permintaan<T>(path: string, opsi: OpsiPermintaan = {}): Promise<T> {
  const respons = await responsBerhasil(path, opsi);
  if (respons.status === 204) return undefined as T;
  return (await respons.json()) as T;
}

/** Mengunduh berkas (misalnya CSV rekap) lalu menyimpannya lewat tautan sementara. */
export async function unduh(path: string, query: Record<string, NilaiQuery>, namaCadangan: string): Promise<string> {
  const respons = await responsBerhasil(path, { query, header: { Accept: "text/csv" } });
  const cocok = /filename="([^"]+)"/.exec(respons.headers.get("Content-Disposition") ?? "");
  const nama = cocok?.[1] ?? namaCadangan;
  const alamat = URL.createObjectURL(await respons.blob());
  const tautan = document.createElement("a");
  tautan.href = alamat;
  tautan.download = nama;
  tautan.click();
  URL.revokeObjectURL(alamat);
  return nama;
}
