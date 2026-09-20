"use client";

import Link from "next/link";
import { type FormEvent, useState } from "react";
import { Button } from "@/components/ui/button";
import { ForgotPasswordPayloadSchema } from "@/lib/schemas/triase.schema";

/**
 * ForgotPasswordFormClient - "use client": STUB fungsional. Endpoint yang
 * dipanggil (POST /api/auth/forgot-password) tidak benar-benar mengirim
 * email — lihat komentar di Route Handler-nya untuk alasan lengkap.
 * Perilaku UI (pesan sukses generik, tanpa membocorkan apakah email
 * terdaftar) tetap realistis meniru sistem produksi sungguhan.
 */
export function ForgotPasswordFormClient() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);

    const parsed = ForgotPasswordPayloadSchema.safeParse({ email });
    if (!parsed.success) {
      setError(parsed.error.issues[0]?.message ?? "Format email tidak valid.");
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await fetch("/api/auth/forgot-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(parsed.data),
      });
      if (!res.ok) throw new Error("Gagal memproses permintaan.");
      setSubmitted(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal memproses permintaan.");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (submitted) {
    return (
      <div className="space-y-4">
        <p
          className="text-sm text-emerald-800 bg-emerald-50 border border-emerald-200 rounded-lg px-4 py-3"
          role="status"
        >
          Jika email tersebut terdaftar, instruksi reset password telah dikirim.
        </p>
        <Link href="/login" className="text-sm text-blue-600 hover:underline inline-block">
          ← Kembali ke halaman masuk
        </Link>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      <div>
        <label htmlFor="email" className="block text-sm font-medium text-slate-700 mb-1">
          Email Akun <span className="text-red-500">*</span>
        </label>
        <input
          type="email"
          id="email"
          name="email"
          required
          autoComplete="username"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm bg-white"
          placeholder="nama@faskes.id"
        />
      </div>

      {error && (
        <p className="text-xs text-red-600" role="alert">
          {error}
        </p>
      )}

      <Button type="submit" size="lg" className="w-full" disabled={isSubmitting}>
        {isSubmitting ? "Memproses…" : "Kirim Instruksi Reset"}
      </Button>

      <Link href="/login" className="text-sm text-blue-600 hover:underline block text-center">
        ← Kembali ke halaman masuk
      </Link>
    </form>
  );
}
