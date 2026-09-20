"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchAntrean, fetchTriageById, submitTriase, submitValidasi } from "@/lib/api-client";
import { antreanKey, triaseDetailKey } from "@/lib/query-keys";
import type { TriageInput, ValidasiTriase } from "@/lib/schemas/triase.schema";

export { antreanKey, triaseDetailKey };

export function useAntreanQuery() {
  return useQuery({
    queryKey: antreanKey(),
    queryFn: fetchAntrean,
    staleTime: 1000 * 30,
  });
}

export function useKritisWatchQuery(enabled: boolean) {
  return useQuery({
    queryKey: antreanKey(),
    queryFn: fetchAntrean,
    enabled,
    refetchInterval: 15_000,
    select: (data) => data.filter((r) => r.riskLevel === "kritis" && r.statusValidasi === "menunggu"),
  });
}

export function useTriaseDetailQuery(idTriase: string) {
  return useQuery({
    queryKey: triaseDetailKey(idTriase),
    queryFn: () => fetchTriageById(idTriase),
    enabled: idTriase.length > 0,
  });
}

export function useSubmitTriaseMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: TriageInput) => submitTriase(input),
    onSuccess: (record) => {
      void queryClient.invalidateQueries({ queryKey: antreanKey() });
      queryClient.setQueryData(triaseDetailKey(record.idTriase), record);
    },
  });
}

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
