import { dehydrate, HydrationBoundary } from "@tanstack/react-query";
import type { Metadata } from "next";
import { PasswordResetRequestsClient } from "@/components/admin/PasswordResetRequestsClient";
import { StaffManagementClient } from "@/components/admin/StaffManagementClient";
import { getQueryClient } from "@/lib/query-client";
import { staffKey } from "@/lib/query-keys";
import { fetchStaffServer } from "@/lib/server-api";
import { getSession } from "@/lib/session";

export const metadata: Metadata = {
  title: "Kelola Akun Staf",
  description: "Registrasi dan pengelolaan akun staf faskes (khusus Admin Faskes).",
};

export default async function AdminStaffPage() {
  const session = await getSession(); 

  if (session?.role !== "admin_faskes") {
    return (
      <div
        className="max-w-3xl rounded-lg border border-amber-300 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/30 p-6"
        role="alert"
      >
        <h1 className="text-lg font-bold text-amber-900 dark:text-amber-300 mb-2">Akses Tidak Diizinkan</h1>
        <p className="text-sm text-amber-800 dark:text-amber-200">
          Hanya Admin Faskes yang berwenang mengelola akun staf. Peran Anda saat ini tidak memiliki akses ke halaman
          ini.
        </p>
      </div>
    );
  }

  const queryClient = getQueryClient();
  await queryClient.prefetchQuery({
    queryKey: staffKey(),
    queryFn: fetchStaffServer,
  });

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <div className="space-y-6">
        <PasswordResetRequestsClient />
        <StaffManagementClient faskesNama={session.faskesNama} currentUserId={session.userId} />
      </div>
    </HydrationBoundary>
  );
}
