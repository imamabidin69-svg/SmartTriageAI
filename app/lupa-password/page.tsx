import type { Metadata } from "next";
import { ForcePublicAppearance } from "@/components/auth/ForcePublicAppearance";
import { ForgotPasswordFormClient } from "@/components/auth/ForgotPasswordFormClient";

export const metadata: Metadata = {
  title: "Lupa Password",
  description: "Minta instruksi reset password untuk akun SmartTriage AI Anda.",
};

/**
 * Sama seperti app/login/page.tsx: SENGAJA tidak ada varian dark: sama
 * sekali (lihat ForcePublicAppearance untuk alasannya).
 */
export default function LupaPasswordPage() {
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
          <h1 className="text-xl font-bold text-slate-900">Lupa Password</h1>
          <p className="text-sm text-slate-500">Masukkan email akun Anda untuk memulai proses reset password.</p>
        </div>

        <section className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm" aria-labelledby="forgot-heading">
          <h2 id="forgot-heading" className="sr-only">
            Form Lupa Password
          </h2>
          <ForgotPasswordFormClient />
        </section>
      </div>
    </main>
  );
}
