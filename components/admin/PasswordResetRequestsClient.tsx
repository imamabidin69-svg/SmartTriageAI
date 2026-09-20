"use client";

import { type FormEvent, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { usePendingPasswordResetsQuery, useResolvePasswordResetMutation } from "@/hooks/useStaffQueries";
import { ResolveResetRequestPayloadSchema } from "@/lib/schemas/password-reset.schema";

function formatWaktu(iso: string): string {
  try {
    return new Date(iso).toLocaleString("id-ID", {
      hour: "2-digit",
      minute: "2-digit",
      day: "2-digit",
      month: "short",
    });
  } catch {
    return iso;
  }
}

/**
 * PasswordResetRequestsClient - "use client": daftar permintaan reset
 * password yang menunggu ditindaklanjuti Admin Faskes (lihat
 * lib/data/password-reset-store.ts untuk konteks kenapa antrean ini ada).
 * Hanya dirender saat role === admin_faskes (lihat pemanggilnya).
 */
export function PasswordResetRequestsClient() {
  const { data: requests, isPending } = usePendingPasswordResetsQuery(true);
  const resolveMutation = useResolvePasswordResetMutation();
  const [activeRequestId, setActiveRequestId] = useState<string | null>(null);
  const [fieldError, setFieldError] = useState<string | null>(null);

  if (isPending || !requests || requests.length === 0) return null;

  function handleSubmit(e: FormEvent<HTMLFormElement>, requestId: string) {
    e.preventDefault();
    setFieldError(null);
    const fd = new FormData(e.currentTarget);
    const parsed = ResolveResetRequestPayloadSchema.safeParse({
      passwordBaru: fd.get("passwordBaru")?.toString() ?? "",
    });
    if (!parsed.success) {
      setFieldError(parsed.error.issues[0]?.message ?? "Password baru tidak valid.");
      return;
    }
    resolveMutation.mutate(
      { id: requestId, passwordBaru: parsed.data.passwordBaru },
      {
        onSuccess: () => setActiveRequestId(null),
        onError: (err) => setFieldError(err instanceof Error ? err.message : "Gagal menyelesaikan permintaan."),
      },
    );
  }

  return (
    <Card emphasis="critical" className="space-y-3" aria-labelledby="reset-requests-heading">
      <h2 id="reset-requests-heading" className="font-semibold text-red-800 dark:text-red-300">
        🔔 {requests.length} Permintaan Reset Password Menunggu
      </h2>
      <ul className="space-y-2">
        {requests.map((r) => (
          <li key={r.id} className="rounded-lg border border-red-200 dark:border-red-900 p-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <p className="text-sm font-medium text-slate-900 dark:text-slate-200">{r.userNama}</p>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {r.userEmail} &middot; diajukan {formatWaktu(r.requestedAt)}
                </p>
              </div>
              <Button
                type="button"
                variant="destructive"
                size="sm"
                onClick={() => {
                  setActiveRequestId((cur) => (cur === r.id ? null : r.id));
                  setFieldError(null);
                }}
              >
                {activeRequestId === r.id ? "Batal" : "Reset Password"}
              </Button>
            </div>

            {activeRequestId === r.id && (
              <form onSubmit={(e) => handleSubmit(e, r.id)} className="mt-3 flex flex-wrap items-end gap-2">
                <div className="flex-1 min-w-[200px]">
                  <label
                    htmlFor={`passwordBaru-${r.id}`}
                    className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1"
                  >
                    Password Baru
                  </label>
                  <input
                    type="text"
                    id={`passwordBaru-${r.id}`}
                    name="passwordBaru"
                    required
                    className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-sm bg-white dark:bg-slate-900 dark:text-slate-200 font-mono"
                    placeholder="Minimal 8 karakter"
                  />
                </div>
                <Button type="submit" size="sm" disabled={resolveMutation.isPending}>
                  {resolveMutation.isPending ? "Menyimpan…" : "Simpan"}
                </Button>
              </form>
            )}
            {activeRequestId === r.id && fieldError && (
              <p className="text-xs text-red-600 mt-1" role="alert">
                {fieldError}
              </p>
            )}
          </li>
        ))}
      </ul>
      <p className="text-xs text-red-700 dark:text-red-400">
        Sampaikan password baru ini kepada staf terkait secara langsung/aman (bukan lewat kanal publik).
      </p>
    </Card>
  );
}
