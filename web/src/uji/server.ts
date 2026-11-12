import { HttpResponse, http } from "msw";
import { setupServer } from "msw/node";
import type { Konfigurasi, Pengguna, Rekap, Staf } from "@/api/tipe";

export const API = "/api/v1";

export const ADMIN: Pengguna = {
  id_pengguna: "a0000000-0000-4000-8000-000000000001",
  nama: "dr. Arif Hidayat",
  email: "admin@smarttriage.demo",
  peran: "admin",
  is_active: true,
};

export const DAFTAR_STAF: Staf[] = [
  { ...ADMIN, created_at: "2026-10-01T02:00:00+00:00" },
  {
    id_pengguna: "b0000000-0000-4000-8000-000000000002",
    nama: "Sari Perawat",
    email: "sari@smarttriage.demo",
    peran: "perawat",
    is_active: true,
    created_at: "2026-10-02T02:00:00+00:00",
  },
  {
    id_pengguna: "c0000000-0000-4000-8000-000000000003",
    nama: "Budi Dokter",
    email: "budi@smarttriage.demo",
    peran: "dokter",
    is_active: false,
    created_at: "2026-10-03T02:00:00+00:00",
  },
];

export const KONFIGURASI: Konfigurasi = {
  versi_model: "rf-icu-physionet2019-v1",
  ambang_kritis: 7,
  ambang_tinggi: 5,
  ambang_sedang: 3,
  batas_tunggu_kritis: 15,
  batas_tunggu_tinggi: 30,
  batas_tunggu_sedang: 60,
  batas_tunggu_rendah: 120,
  ambang_keyakinan: 0.85,
  versi_model_termuat: "rf-icu-physionet2019-v1",
};

export const REKAP: Rekap = {
  dari: "2026-10-11",
  sampai: "2026-10-17",
  total_triase: 142,
  per_level: { kritis: 8, tinggi: 30, sedang: 54, rendah: 50 },
  rata_tunggu_menit: { kritis: 2.5, tinggi: 9, sedang: 25.4, rendah: null },
  persen_koreksi: 6.3,
  triase_ulang: 17,
  akurasi_pemindaian: 96.4,
};

export function problem(status: number, isi: Record<string, unknown>, headers?: Record<string, string>) {
  return HttpResponse.json(
    { type: "about:blank", title: "Galat", status, ...isi },
    { status, headers: { "Content-Type": "application/problem+json", ...headers } },
  );
}

export const handlerBawaan = [
  http.get(`${API}/auth/me`, () => HttpResponse.json(ADMIN)),
  http.post(`${API}/auth/logout`, () => new HttpResponse(null, { status: 204 })),
  http.get(`${API}/admin/staf`, () => HttpResponse.json({ items: DAFTAR_STAF })),
  http.get(`${API}/admin/konfigurasi`, () => HttpResponse.json(KONFIGURASI)),
  http.get(`${API}/health`, () =>
    HttpResponse.json({
      status: "ok",
      komponen: { database: "ok", model_perburukan: "ok", pembaca_layar: "ok", groq: "ok" },
    }),
  ),
  http.get(`${API}/rekap`, () => HttpResponse.json(REKAP)),
  http.get(`${API}/admin/log-audit`, () => HttpResponse.json({ items: [], kursor_berikutnya: null })),
];

export const server = setupServer(...handlerBawaan);
