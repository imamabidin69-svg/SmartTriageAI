import { redirect } from "next/navigation";
import { DashboardHeaderClient } from "@/components/dashboard/DashboardHeaderClient";
import { DashboardSidebarNavClient } from "@/components/dashboard/DashboardSidebarNavClient";
import { KritisNotificationWatcher } from "@/components/dashboard/KritisNotificationWatcher";
import { getSession } from "@/lib/session";

/**
 * app/(protected)/layout.tsx - Nested Layout (Modul 6, Bab D) yang dipakai
 * BERSAMA oleh /dashboard, /triase/baru, dan /triase/[id] lewat Route Group
 * "(protected)" (nama dalam kurung tidak muncul di URL). Karena ketiganya
 * berbagi layout yang sama, Next.js TIDAK me-remount elemen ini saat
 * pengguna berpindah antar rute tersebut — status sidebar (Zustand,
 * Client UI State) tetap terjaga tanpa berkedip/reset.
 *
 * Server Component ini sendiri melakukan pekerjaan berat (baca cookie sesi)
 * di server; hanya sidebar interaktifnya yang dilimpahkan ke Client
 * Component (Leaf Component pattern, Modul 6 Bab C).
 */
export default async function ProtectedLayout({ children }: { children: React.ReactNode }) {
  const session = await getSession();
  if (!session) {
    redirect("/login?auth_error=1");
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-900">
      <KritisNotificationWatcher enabled={session.role === "dokter_pj"} />
      <DashboardHeaderClient session={session} />
      <div className="flex-1 flex flex-col md:flex-row max-w-6xl mx-auto w-full">
        <DashboardSidebarNavClient role={session.role} />
        <main className="flex-1 p-6 min-w-0">{children}</main>
      </div>
    </div>
  );
}
