import { type FormEvent, useState } from "react";
import { z } from "zod";
import { useGantiPassword } from "@/api/admin";
import { ProblemError, pesanError } from "@/api/klien";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Isian } from "@/components/ui/isian";
import { useNotifikasi } from "@/lib/notifikasi";
import { galatZod } from "@/lib/validasi";

// Aturan sama dengan GantiPasswordRequest di backend: 8-128 karakter dan berbeda dari password lama.
const skema = z
  .object({
    password_lama: z.string().min(1, "Password lama wajib diisi."),
    password_baru: z
      .string()
      .min(8, "Password baru minimal 8 karakter.")
      .max(128, "Password baru maksimal 128 karakter."),
    konfirmasi: z.string(),
  })
  .refine((d) => d.password_baru !== d.password_lama, {
    path: ["password_baru"],
    message: "Password baru harus berbeda dari password lama.",
  })
  .refine((d) => d.password_baru === d.konfirmasi, {
    path: ["konfirmasi"],
    message: "Konfirmasi password tidak sama.",
  });

const KOSONG = { password_lama: "", password_baru: "", konfirmasi: "" };

export function HalamanGantiPassword() {
  const [isian, setIsian] = useState(KOSONG);
  const [galatField, setGalatField] = useState<Record<string, string>>({});
  const [galat, setGalat] = useState<string>();
  const ganti = useGantiPassword();
  const tampilkan = useNotifikasi((s) => s.tampilkan);

  function ubah(nama: keyof typeof KOSONG, nilai: string) {
    setIsian((lama) => ({ ...lama, [nama]: nilai }));
  }

  function kirim(event: FormEvent) {
    event.preventDefault();
    setGalat(undefined);
    const hasil = skema.safeParse(isian);
    if (!hasil.success) {
      setGalatField(galatZod(hasil.error));
      return;
    }
    setGalatField({});
    ganti.mutate(
      { password_lama: isian.password_lama, password_baru: isian.password_baru },
      {
        onSuccess: () => {
          setIsian(KOSONG);
          tampilkan("Password berhasil diganti.");
        },
        onError: (e) => {
          if (e instanceof ProblemError) setGalatField(e.pesanField);
          setGalat(pesanError(e));
        },
      },
    );
  }

  return (
    <div className="max-w-lg">
      <h1 className="text-2xl font-semibold text-slate-900">Ganti password</h1>
      <p className="mt-1 mb-6 text-sm text-slate-600">Password baru berlaku untuk login berikutnya.</p>
      <Card>
        <form onSubmit={kirim} noValidate className="space-y-4">
          {galat ? <Alert jenis="galat">{galat}</Alert> : null}
          <Isian
            label="Password lama"
            type="password"
            autoComplete="current-password"
            value={isian.password_lama}
            onChange={(e) => ubah("password_lama", e.target.value)}
            galat={galatField.password_lama}
          />
          <Isian
            label="Password baru"
            type="password"
            autoComplete="new-password"
            petunjuk="8 sampai 128 karakter."
            value={isian.password_baru}
            onChange={(e) => ubah("password_baru", e.target.value)}
            galat={galatField.password_baru}
          />
          <Isian
            label="Ulangi password baru"
            type="password"
            autoComplete="new-password"
            value={isian.konfirmasi}
            onChange={(e) => ubah("konfirmasi", e.target.value)}
            galat={galatField.konfirmasi}
          />
          <Button type="submit" disabled={ganti.isPending}>
            {ganti.isPending ? "Menyimpan..." : "Simpan password baru"}
          </Button>
        </form>
      </Card>
    </div>
  );
}
