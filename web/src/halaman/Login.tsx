import { LockSimple } from "@phosphor-icons/react";
import { useQueryClient } from "@tanstack/react-query";
import { type FormEvent, useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router";
import { z } from "zod";
import { keluar, kunci, masuk, useSaya } from "@/api/admin";
import { ProblemError, pesanError } from "@/api/klien";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Isian } from "@/components/ui/isian";
import { LogoAplikasi } from "@/components/ui/logo";
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
    <div className="flex min-h-screen items-center justify-center px-4 py-10">
      <div className="w-full max-w-[400px] rounded-md border border-garis bg-white px-7 pt-7 pb-6">
        <div className="flex items-center gap-3">
          <LogoAplikasi ukuran={44} />
          <div className="leading-tight">
            <p className="text-[17px] font-bold">SmartTriage AI</p>
            <p className="text-sm text-teks-2">Instalasi Gawat Darurat</p>
          </div>
        </div>
        <h1 className="mt-8 text-2xl font-bold">Masuk admin IGD</h1>
        <p className="mt-1 mb-6 text-[15px] text-teks-2">Gunakan akun admin yang terdaftar.</p>
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
          <Button type="submit" size="lg" className="w-full" disabled={mengirim}>
            {mengirim ? "Memeriksa..." : "Masuk"}
          </Button>
        </form>
        <p className="mt-6 flex gap-2 border-t border-garis-2 pt-4 text-[13px] leading-relaxed text-teks-3">
          <LockSimple size={16} className="mt-0.5 shrink-0" aria-hidden />
          Data pasien bersifat rahasia. Jangan bagikan akun Anda kepada siapa pun.
        </p>
      </div>
    </div>
  );
}
