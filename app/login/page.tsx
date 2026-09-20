import type { Metadata } from "next";
import { ForcePublicAppearance } from "@/components/auth/ForcePublicAppearance";
import { LoginFormClient } from "@/components/auth/LoginFormClient";

export const metadata: Metadata = {
  title: "Masuk",
  description: "Masuk ke SmartTriage AI menggunakan email dan password akun staf faskes Anda.",
};

interface LoginPageProps {
  searchParams: Promise<{ auth_error?: string }>;
}

/**
 * app/login/page.tsx - Server Component. Hanya bagian form yang interaktif
 * (LoginFormClient) yang dibatasi "use client"; struktur halaman, heading,
 * dan pesan bantuan tetap dirender di server (zero JS tambahan untuk itu).
 *
 * Halaman ini SENGAJA tidak punya varian dark: sama sekali — satu tampilan
 * tetap untuk semua orang (lihat ForcePublicAppearance untuk alasannya).
 */
export default async function LoginPage({ searchParams }: LoginPageProps) {
  const { auth_error } = await searchParams;

  return (
    <main className="min-h-screen flex items-center justify-center px-4 bg-slate-50">
      <ForcePublicAppearance />
      <div className="w-full max-w-md">
        <div className="text-center mb-6">
          <div
            className="w-14 h-14 bg-blue-600 rounded-xl mx-auto flex items-center justify-center font-bold text-2xl text-white mb-3"
            aria-hidden="true"
          >
            ST
          </div>
          <h1 className="text-xl font-bold text-slate-900">SmartTriage AI</h1>
          <p className="text-sm text-slate-500">Sistem Bantu Triase Pasien — IGD &amp; Puskesmas</p>
        </div>

        <section className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm" aria-labelledby="login-heading">
          <h2 id="login-heading" className="text-lg font-bold text-slate-900 mb-4 border-b border-slate-200 pb-2">
            Masuk ke Sistem
          </h2>

          {auth_error && (
            <p
              className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mb-4"
              role="alert"
            >
              Sesi Anda berakhir atau belum masuk. Silakan masuk kembali untuk mengakses halaman tersebut.
            </p>
          )}

          <LoginFormClient />
        </section>
      </div>
    </main>
  );
}
