import { redirect } from "next/navigation";
import { getHomeRouteForRole } from "@/lib/role-routes";
import { getSession } from "@/lib/session";

/**
 * Halaman akar "/" - Server Component murni, membaca sesi lalu redirect.
 * Tidak ada UI yang dirender di sini sama sekali (zero client JS).
 */
export default async function RootPage() {
  const session = await getSession();
  if (!session) {
    redirect("/login");
  }
  redirect(getHomeRouteForRole(session.role));
}
