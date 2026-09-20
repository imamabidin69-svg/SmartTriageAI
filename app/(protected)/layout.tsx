import { redirect } from "next/navigation";
import { DashboardHeaderClient } from "@/components/dashboard/DashboardHeaderClient";
import { DashboardSidebarNavClient } from "@/components/dashboard/DashboardSidebarNavClient";
import { KritisNotificationWatcher } from "@/components/dashboard/KritisNotificationWatcher";
import { getSession } from "@/lib/session";

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
