import type { Metadata } from "next";
import { LoginFormClient } from "@/components/auth/LoginFormClient";

export const metadata: Metadata = {
  title: "Masuk",
  description: "Masuk ke SmartTriage AI menggunakan email dan password akun staf faskes Anda.",
};

interface LoginPageProps {
  searchParams: Promise<{ auth_error?: string }>;
}

export default async function LoginPage({ searchParams }: LoginPageProps) {
  const { auth_error } = await searchParams;

  return (
    <main
      id="konten-utama"
      tabIndex={-1}
      className="min-h-dvh flex items-center justify-center px-4 bg-slate-50 dark:bg-slate-900 focus:outline-none"
    >
      <div className="w-full max-w-md">
        <div className="text-center mb-6">
          <div
            className="w-14 h-14 bg-blue-600 rounded-xl mx-auto flex items-center justify-center font-bold text-2xl text-white mb-3"
            aria-hidden="true"
          >
            ST
          </div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">SmartTriage AI</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Sistem Bantu Triase Pasien untuk IGD &amp; Puskesmas
          </p>
        </div>

        <section
          className="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm"
          aria-labelledby="login-heading"
        >
          <h2
            id="login-heading"
            className="text-lg font-bold text-slate-900 dark:text-slate-100 mb-4 border-b border-slate-200 dark:border-slate-700 pb-2"
          >
            Masuk ke Sistem
          </h2>

          {auth_error && (
            <p
              className="text-xs text-amber-800 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-lg px-3 py-2 mb-4"
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
