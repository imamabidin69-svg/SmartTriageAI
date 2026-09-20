"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";
import { Button } from "@/components/ui/button";
import { getHomeRouteForRole } from "@/lib/role-routes";
import { LoginPayloadSchema } from "@/lib/schemas/triase.schema";

/**
 * LoginFormClient - "use client": form login email+password sungguhan.
 * Menggantikan versi lama (pilih role dari dropdown) sepenuhnya — kini
 * setiap staf WAJIB punya akun sungguhan yang didaftarkan Admin Faskesnya
 * (lihat components/admin/StaffManagementClient.tsx), tidak ada lagi jalur
 * "demo cepat" tanpa kredensial.
 */
export function LoginFormClient() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);

    const parsed = LoginPayloadSchema.safeParse({ email, password });
    if (!parsed.success) {
      setError(parsed.error.issues[0]?.message ?? "Email atau password tidak valid.");
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(parsed.data),
      });
      if (!res.ok) {
        const body: unknown = await res.json().catch(() => null);
        const message =
          body && typeof body === "object" && "error" in body && typeof body.error === "string"
            ? body.error
            : "Gagal masuk ke sistem.";
        throw new Error(message);
      }
      const session: unknown = await res.json().catch(() => null);
      const role =
        session && typeof session === "object" && "role" in session && typeof session.role === "string"
          ? session.role
          : null;
      router.push(getHomeRouteForRole(role));
      router.refresh(); // memastikan Server Component (layout/page) membaca ulang cookie sesi
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal masuk ke sistem.");
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      <div>
        <label htmlFor="email" className="block text-sm font-medium text-slate-700 mb-1">
          Email <span className="text-red-500">*</span>
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

      <div>
        <div className="flex items-center justify-between mb-1">
          <label htmlFor="password" className="block text-sm font-medium text-slate-700">
            Password <span className="text-red-500">*</span>
          </label>
          <Link href="/lupa-password" className="text-xs text-blue-600 hover:underline">
            Lupa password?
          </Link>
        </div>
        <input
          type="password"
          id="password"
          name="password"
          required
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm bg-white"
          placeholder="••••••••"
        />
      </div>

      {error && (
        <p className="text-xs text-red-600" role="alert">
          {error}
        </p>
      )}

      <Button type="submit" size="lg" className="w-full" disabled={isSubmitting}>
        {isSubmitting ? "Memproses…" : "Masuk"}
      </Button>

      <p className="text-xs text-slate-400 text-center">
        Belum punya akun? Registrasi hanya dapat dilakukan oleh Admin Faskes tempat Anda bertugas.
      </p>
    </form>
  );
}
