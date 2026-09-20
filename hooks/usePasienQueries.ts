"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchPasien, registerPasien } from "@/lib/api-client";
import { pasienKey } from "@/lib/query-keys";
import type { RegisterPasienPayload } from "@/lib/schemas/pasien.schema";

export function usePasienQuery() {
  return useQuery({
    queryKey: pasienKey(),
    queryFn: fetchPasien,
  });
}

export function useRegisterPasienMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: RegisterPasienPayload) => registerPasien(input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: pasienKey() });
    },
  });
}
