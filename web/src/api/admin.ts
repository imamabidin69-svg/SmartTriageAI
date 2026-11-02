/** Query dan mutation TanStack Query untuk halaman admin (FR-01, FR-05, FR-07, FR-09). */
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ProblemError, permintaan, unduh } from "./klien";
import type {
  AksiAudit,
  HalamanLogAudit,
  Health,
  Konfigurasi,
  KonfigurasiPatch,
  Pengguna,
  Rekap,
  SesiLogin,
  Staf,
  StafBaru,
  StafDisimpan,
  StafPatch,
} from "./tipe";

export const kunci = {
  saya: ["saya"] as const,
  staf: ["staf"] as const,
  konfigurasi: ["konfigurasi"] as const,
  health: ["health"] as const,
  rekap: (dari?: string, sampai?: string) => ["rekap", dari ?? null, sampai ?? null] as const,
  logAudit: (filter: FilterLogAudit) => ["log-audit", filter] as const,
};

/** Pengguna yang sedang masuk, atau null bila belum masuk atau sesinya habis. */
export function useSaya() {
  return useQuery({
    queryKey: kunci.saya,
    queryFn: async (): Promise<Pengguna | null> => {
      try {
        return await permintaan<Pengguna>("/auth/me");
      } catch (galat) {
        if (galat instanceof ProblemError && galat.status === 401) return null;
        throw galat;
      }
    },
    staleTime: 60_000,
  });
}

export function masuk(email: string, password: string) {
  return permintaan<SesiLogin>("/auth/login", { method: "POST", json: { email, password } });
}

export async function keluar() {
  try {
    await permintaan<void>("/auth/logout", { method: "POST", csrf: "refresh", bolehRefresh: false });
  } catch (galat) {
    // Sesi yang sudah habis tetap dianggap berhasil keluar.
    if (!(galat instanceof ProblemError && galat.status === 401)) throw galat;
  }
}

export function useKeluar() {
  const klien = useQueryClient();
  return useMutation({
    mutationFn: keluar,
    onSettled: () => {
      klien.clear();
      klien.setQueryData(kunci.saya, null);
    },
  });
}

export function useGantiPassword() {
  return useMutation({
    mutationFn: (isi: { password_lama: string; password_baru: string }) =>
      permintaan<void>("/auth/password", { method: "PATCH", json: isi }),
  });
}

// ---------------------------------------------------------------- staf

export function useStaf() {
  return useQuery({ queryKey: kunci.staf, queryFn: () => permintaan<{ items: Staf[] }>("/admin/staf") });
}

export function useTambahStaf() {
  const klien = useQueryClient();
  return useMutation({
    mutationFn: (isi: StafBaru) => permintaan<StafDisimpan>("/admin/staf", { method: "POST", json: isi }),
    onSuccess: () => klien.invalidateQueries({ queryKey: kunci.staf }),
  });
}

export function useUbahStaf() {
  const klien = useQueryClient();
  return useMutation({
    mutationFn: ({ id, isi }: { id: string; isi: StafPatch }) =>
      permintaan<StafDisimpan>(`/admin/staf/${id}`, { method: "PATCH", json: isi }),
    onSuccess: () => klien.invalidateQueries({ queryKey: kunci.staf }),
  });
}

// ---------------------------------------------------------------- konfigurasi dan kesehatan

export function useKonfigurasi() {
  return useQuery({ queryKey: kunci.konfigurasi, queryFn: () => permintaan<Konfigurasi>("/admin/konfigurasi") });
}

export function useSimpanKonfigurasi() {
  const klien = useQueryClient();
  return useMutation({
    mutationFn: (isi: KonfigurasiPatch) =>
      permintaan<Konfigurasi>("/admin/konfigurasi", { method: "PATCH", json: isi }),
    onSuccess: (data) => klien.setQueryData(kunci.konfigurasi, data),
  });
}

export function useHealth() {
  return useQuery({
    queryKey: kunci.health,
    queryFn: async (): Promise<Health> => {
      try {
        return await permintaan<Health>("/health");
      } catch (galat) {
        // 503 tetap berisi status per komponen.
        if (galat instanceof ProblemError && galat.isi.komponen) return galat.isi as unknown as Health;
        throw galat;
      }
    },
  });
}

// ---------------------------------------------------------------- rekap dan log audit

export function useRekap(dari?: string, sampai?: string) {
  return useQuery({
    queryKey: kunci.rekap(dari, sampai),
    queryFn: () => permintaan<Rekap>("/rekap", { query: { dari, sampai } }),
  });
}

export function unduhRekapCsv(dari?: string, sampai?: string) {
  return unduh("/rekap", { dari, sampai, format: "csv" }, "rekap-smarttriage.csv");
}

export interface FilterLogAudit {
  dari?: string;
  sampai?: string;
  aksi?: AksiAudit;
  id_aktor?: string;
}

export function useLogAudit(filter: FilterLogAudit) {
  return useInfiniteQuery({
    queryKey: kunci.logAudit(filter),
    queryFn: ({ pageParam }) =>
      permintaan<HalamanLogAudit>("/admin/log-audit", { query: { ...filter, kursor: pageParam, ukuran: 50 } }),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (halaman) => halaman.kursor_berikutnya ?? undefined,
  });
}
