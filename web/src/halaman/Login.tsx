import { useQueryClient } from "@tanstack/react-query";
import { type FormEvent, useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router";
import { z } from "zod";
import { keluar, kunci, masuk, useSaya } from "@/api/admin";
import { ProblemError, pesanError } from "@/api/klien";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Isian } from "@/components/ui/isian";
import { PESAN_BUKAN_ADMIN } from "@/layout/PenjagaAdmin";
import { galatZod } from "@/lib/validasi";

const skemaLogin = z.object({
  email: z.string().trim().min(1, "Email wajib diisi.").email("Format email tidak valid."),
  password: z.string().min(1, "Password wajib diisi."),
});

interface StateLokasi {
  dari?: string;
  pesan?: string;
}

export function HalamanLogin() {
  const lokasi = useLocation();
  const state = (lokasi.state ?? {}) as StateLokasi;
  const navigasi = useNavigate();
  const klien = useQueryClient();
  const saya = useSaya();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [galatField, setGalatField] = useState<Record<string, string>>({});
  const [galat, setGalat] = useState<string | undefined>(state.pesan);
  const [mengirim, setMengirim] = useState(false);

  if (saya.data?.peran === "admin") return <Navigate to={state.dari ?? "/staf"} replace />;

  async function kirim(event: FormEvent) {
    event.preventDefault();
    const hasil = skemaLogin.safeParse({ email, password });
    if (!hasil.success) {
      setGalatField(galatZod(hasil.error));
      return;
    }
    setGalatField({});
    setGalat(undefined);
    setMengirim(true);
    try {
      const sesi = await masuk(hasil.data.email, hasil.data.password);
      if (sesi.pengguna.peran !== "admin") {
        // Keputusan W4: web khusus admin. Cookie yang terlanjur dibuat langsung dihapus.
        await keluar().catch(() => undefined);
        setGalat(PESAN_BUKAN_ADMIN);
        return;
      }
      klien.setQueryData(kunci.saya, sesi.pengguna);
      navigasi(state.dari ?? "/staf", { replace: true });
    } catch (e) {
      if (e instanceof ProblemError) setGalatField(e.pesanField);
      setGalat(pesanError(e));
    } finally {
      setMengirim(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex items-center justify-center gap-3 text-xl font-semibold text-slate-900">
          <span aria-hidden className="size-8 rounded-md bg-blue-600" />
          SmartTriage AI
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h1 className="text-lg font-semibold text-slate-900">Masuk admin IGD</h1>
          <p className="mt-1 mb-5 text-sm text-slate-600">Gunakan akun admin yang terdaftar.</p>
          <form onSubmit={kirim} noValidate className="space-y-4">
            {galat ? <Alert jenis="galat">{galat}</Alert> : null}
            <Isian
              label="Email"
              type="email"
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              galat={galatField.email}
            />
            <Isian
              label="Password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              galat={galatField.password}
            />
            <Button type="submit" className="w-full" disabled={mengirim}>
              {mengirim ? "Memeriksa..." : "Masuk"}
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
