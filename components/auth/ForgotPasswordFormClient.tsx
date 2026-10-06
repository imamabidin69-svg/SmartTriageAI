"use client";

import { ArrowLeft } from "@phosphor-icons/react";
import Link from "next/link";
import { type FormEvent, useState } from "react";
import { Button } from "@/components/ui/button";
import { ForgotPasswordPayloadSchema } from "@/lib/schemas/triase.schema";

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
          className="text-sm text-emerald-800 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 rounded-lg px-4 py-3"
          role="status"
        >
          Jika email tersebut terdaftar, instruksi reset password telah dikirim.
        </p>
        <Link
          href="/login"
          className="inline-flex items-center gap-1.5 text-sm text-blue-600 dark:text-blue-400 hover:underline"
        >
          <ArrowLeft size={16} aria-hidden="true" />
          Kembali ke halaman masuk
        </Link>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      <div>
        <label htmlFor="email" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
          Email Akun{" "}
          <span className="text-red-600 dark:text-red-400" aria-hidden="true">
            *
          </span>
        </label>
        <input
          type="email"
          id="email"
          name="email"
          required
          autoComplete="username"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm bg-white dark:bg-slate-900 dark:text-slate-200"
          placeholder="nama@faskes.id"
        />
      </div>

      {error && (
        <p className="text-xs text-red-600 dark:text-red-400" role="alert">
          {error}
        </p>
      )}

      <Button type="submit" size="lg" className="w-full" disabled={isSubmitting}>
        {isSubmitting ? "Memproses…" : "Kirim Instruksi Reset"}
      </Button>

      <Link
        href="/login"
        className="flex items-center justify-center gap-1.5 text-sm text-blue-600 dark:text-blue-400 hover:underline"
      >
        <ArrowLeft size={16} aria-hidden="true" />
        Kembali ke halaman masuk
      </Link>
    </form>
  );
}
