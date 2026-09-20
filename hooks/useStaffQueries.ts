"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createStaff,
  fetchPendingPasswordResets,
  fetchStaff,
  resolvePasswordReset,
  toggleStaffActive,
  updateStaff,
} from "@/lib/api-client";
import { passwordResetsKey, staffKey } from "@/lib/query-keys";
import type { RegisterStaffPayload, UpdateStaffPayload } from "@/lib/schemas/triase.schema";

export function useStaffQuery() {
  return useQuery({
    queryKey: staffKey(),
    queryFn: fetchStaff,
  });
}

export function useCreateStaffMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: RegisterStaffPayload) => createStaff(input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: staffKey() });
    },
  });
}

export function useToggleStaffMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, isActive }: { id: string; isActive: boolean }) => toggleStaffActive(id, isActive),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: staffKey() });
    },
  });
}

export function useUpdateStaffMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: UpdateStaffPayload }) => updateStaff(id, input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: staffKey() });
    },
  });
}

export function usePendingPasswordResetsQuery(enabled: boolean) {
  return useQuery({
    queryKey: passwordResetsKey(),
    queryFn: fetchPendingPasswordResets,
    enabled,
    refetchInterval: 30_000,
  });
}

export function useResolvePasswordResetMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, passwordBaru }: { id: string; passwordBaru: string }) => resolvePasswordReset(id, passwordBaru),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: passwordResetsKey() });
    },
  });
}
