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

/** Server State: daftar staf di faskes Admin yang login. */
export function useStaffQuery() {
  return useQuery({
    queryKey: staffKey(),
    queryFn: fetchStaff,
  });
}

/** Registrasi staf baru, otomatis invalidasi daftar staf setelah berhasil. */
export function useCreateStaffMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: RegisterStaffPayload) => createStaff(input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: staffKey() });
    },
  });
}

/** Aktifkan/nonaktifkan akun staf, otomatis invalidasi daftar staf setelah berhasil. */
export function useToggleStaffMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, isActive }: { id: string; isActive: boolean }) => toggleStaffActive(id, isActive),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: staffKey() });
    },
  });
}

/** Edit info akun staf lain (nama, email, peran), otomatis invalidasi daftar staf setelah berhasil. */
export function useUpdateStaffMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: UpdateStaffPayload }) => updateStaff(id, input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: staffKey() });
    },
  });
}

/** Server State: permintaan reset password PENDING di faskes Admin. Di-refetch berkala untuk notifikasi. */
export function usePendingPasswordResetsQuery(enabled: boolean) {
  return useQuery({
    queryKey: passwordResetsKey(),
    queryFn: fetchPendingPasswordResets,
    enabled,
    refetchInterval: 30_000, // polling ringan setiap 30 detik supaya badge notifikasi cukup real-time
  });
}

/** Menyelesaikan permintaan reset (set password baru), invalidasi daftar permintaan setelah berhasil. */
export function useResolvePasswordResetMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, passwordBaru }: { id: string; passwordBaru: string }) => resolvePasswordReset(id, passwordBaru),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: passwordResetsKey() });
    },
  });
}
