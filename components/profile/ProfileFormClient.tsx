"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";
import { Button } from "@/components/ui/button";
import { useUpdateProfileMutation } from "@/hooks/useProfileQueries";
import { UpdateProfilePayloadSchema } from "@/lib/schemas/triase.schema";

/**
 * ProfileFormClient - "use client": form ubah nama & password akun sendiri.
 * Tersedia untuk SEMUA role yang login (bukan cuma Admin Faskes) — lihat
 * app/api/auth/profile/route.ts untuk alasannya.
 */
export function ProfileFormClient({ namaSaatIni }: { namaSaatIni: string }) {
  const router = useRouter();
  const mutation = useUpdateProfileMutation();
  const [nama, setNama] = useState(namaSaatIni);
  const [passwordSaatIni, setPasswordSaatIni] = useState("");
  const [passwordBaru, setPasswordBaru] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setFieldErrors({});
    setSuccessMessage(null);

    const raw = {
      nama,
      passwordSaatIni: passwordSaatIni || undefined,
      passwordBaru: passwordBaru || undefined,
    };
    const parsed = UpdateProfilePayloadSchema.safeParse(raw);
    if (!parsed.success) {
      const errors: Record<string, string> = {};
      for (const issue of parsed.error.issues) errors[issue.path.join(".")] = issue.message;
      setFieldErrors(errors);
      return;
    }

    mutation.mutate(parsed.data, {
      onSuccess: () => {
        setSuccessMessage("Profil berhasil diperbarui.");
        setPasswordSaatIni("");
        setPasswordBaru("");
        router.refresh(); // Server Component (header/sidebar) baca ulang cookie sesi (nama bisa berubah)
      },
      onError: (err) => {
        setFieldErrors({ passwordSaatIni: err instanceof Error ? err.message : "Gagal memperbarui profil." });
      },
    });
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm space-y-4"
      noValidate
    >
      <div>
        <label htmlFor="nama" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
          Nama Lengkap <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          id="nama"
          name="nama"
          required
          value={nama}
          onChange={(e) => setNama(e.target.value)}
          className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm bg-white dark:bg-slate-900 dark:text-slate-200"
        />
        {fieldErrors.nama && (
          <p className="text-xs text-red-600 mt-1" role="alert">
            {fieldErrors.nama}
          </p>
        )}
      </div>

      <div className="border-t border-slate-200 dark:border-slate-700 pt-4">
        <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
          Ganti Password{" "}
          <span className="text-xs font-normal text-slate-400">(kosongkan jika tidak ingin mengganti)</span>
        </p>

        <div className="space-y-3">
          <div>
            <label
              htmlFor="passwordSaatIni"
              className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1"
            >
              Password Saat Ini
            </label>
            <input
              type="password"
              id="passwordSaatIni"
              name="passwordSaatIni"
              autoComplete="current-password"
              value={passwordSaatIni}
              onChange={(e) => setPasswordSaatIni(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm bg-white dark:bg-slate-900 dark:text-slate-200"
            />
            {fieldErrors.passwordSaatIni && (
              <p className="text-xs text-red-600 mt-1" role="alert">
                {fieldErrors.passwordSaatIni}
              </p>
            )}
          </div>

          <div>
            <label htmlFor="passwordBaru" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Password Baru
            </label>
            <input
              type="password"
              id="passwordBaru"
              name="passwordBaru"
              autoComplete="new-password"
              value={passwordBaru}
              onChange={(e) => setPasswordBaru(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm bg-white dark:bg-slate-900 dark:text-slate-200"
            />
            {fieldErrors.passwordBaru && (
              <p className="text-xs text-red-600 mt-1" role="alert">
                {fieldErrors.passwordBaru}
              </p>
            )}
          </div>
        </div>
      </div>

      {successMessage && (
        <p className="text-sm text-emerald-700 dark:text-emerald-400" role="status">
          {successMessage}
        </p>
      )}

      <Button type="submit" disabled={mutation.isPending}>
        {mutation.isPending ? "Menyimpan…" : "Simpan Perubahan"}
      </Button>
    </form>
  );
}
