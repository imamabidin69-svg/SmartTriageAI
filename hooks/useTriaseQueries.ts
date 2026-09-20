"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchAntrean, fetchTriageById, submitTriase, submitValidasi } from "@/lib/api-client";
import { antreanKey, triaseDetailKey } from "@/lib/query-keys";
import type { TriageInput, ValidasiTriase } from "@/lib/schemas/triase.schema";

export { antreanKey, triaseDetailKey };

/** FR-09: Server State untuk Dashboard Antrean. */
export function useAntreanQuery() {
  return useQuery({
    queryKey: antreanKey(),
    queryFn: fetchAntrean,
    staleTime: 1000 * 30, // antrean gawat darurat perlu relatif segar
  });
}

/**
 * Polling ringan untuk notifikasi kasus kritis (DPJ) - dipisah dari
 * useAntreanQuery (staleTime 30 detik, tidak auto-refetch) karena
 * notifikasi butuh deteksi kedatangan kasus baru secara proaktif, bukan
 * cuma segar saat halaman dibuka. refetchInterval 15 detik dipilih lebih
 * ketat dari staleTime dashboard biasa karena sifatnya time-sensitive.
 */
export function useKritisWatchQuery(enabled: boolean) {
  return useQuery({
    queryKey: antreanKey(),
    queryFn: fetchAntrean,
    enabled,
    refetchInterval: 15_000,
    select: (data) => data.filter((r) => r.riskLevel === "kritis" && r.statusValidasi === "menunggu"),
  });
}

/** Server State untuk detail satu hasil triase (Hasil & Penjelasan AI). */
export function useTriaseDetailQuery(idTriase: string) {
  return useQuery({
    queryKey: triaseDetailKey(idTriase),
    queryFn: () => fetchTriageById(idTriase),
    enabled: idTriase.length > 0,
  });
}

/** FR-03/04/05: mutasi submit form triase baru, otomatis invalidasi cache antrean. */
export function useSubmitTriaseMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: TriageInput) => submitTriase(input),
    onSuccess: (record) => {
      // Invalidasi daftar antrean agar dashboard langsung menampilkan data terbaru,
      // dan tanam hasilnya langsung ke cache detail agar halaman hasil tidak perlu fetch ulang.
      void queryClient.invalidateQueries({ queryKey: antreanKey() });
      queryClient.setQueryData(triaseDetailKey(record.idTriase), record);
    },
  });
}

/** FR-06/FR-07: mutasi Setujui/Koreksi, invalidasi cache antrean + detail terkait. */
export function useSubmitValidasiMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ValidasiTriase) => submitValidasi(payload),
    onSuccess: (record) => {
      void queryClient.invalidateQueries({ queryKey: antreanKey() });
      queryClient.setQueryData(triaseDetailKey(record.idTriase), record);
    },
  });
}
