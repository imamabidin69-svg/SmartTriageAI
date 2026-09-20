import type { Metadata } from "next";
import { ProfileFormClient } from "@/components/profile/ProfileFormClient";
import { getSession } from "@/lib/session";

export const metadata: Metadata = {
  title: "Profil Saya",
  description: "Ubah nama dan password akun Anda.",
};

export default async function ProfilPage() {
  const session = await getSession();

  return (
    <div className="max-w-lg">
      <h1 className="text-xl font-bold text-slate-900 dark:text-slate-200 mb-1">Profil Saya</h1>
      <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">
        {session?.faskesNama} — kelola nama dan password akun Anda.
      </p>
      <ProfileFormClient namaSaatIni={session?.nama ?? ""} />
    </div>
  );
}
