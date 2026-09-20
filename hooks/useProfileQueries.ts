"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { updateProfile } from "@/lib/api-client";
import type { UpdateProfilePayload } from "@/lib/schemas/triase.schema";

/**
 * useUpdateProfileMutation - tersedia untuk semua role. Setelah berhasil,
 * router.refresh() (dipanggil dari komponen pemanggil) akan membuat Server
 * Component membaca ulang cookie sesi yang baru (nama bisa berubah, dan
 * header/sidebar membaca nama dari sesi, bukan dari query ini).
 */
export function useUpdateProfileMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: UpdateProfilePayload) => updateProfile(input),
    onSuccess: () => {
      // Tidak ada query key khusus "profile" yang di-cache di tempat lain saat
      // ini, tapi invalidateQueries({}) longgar ini aman & murah untuk
      // memastikan data terkait (mis. daftar staf, jika admin mengganti nama
      // sendiri) ikut segar.
      void queryClient.invalidateQueries({ queryKey: ["staff"] });
    },
  });
}
