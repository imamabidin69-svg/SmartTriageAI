import { redirect } from "next/navigation";
import { getHomeRouteForRole } from "@/lib/role-routes";
import { getSession } from "@/lib/session";

export default async function RootPage() {
  const session = await getSession();
  if (!session) {
    redirect("/login");
  }
  redirect(getHomeRouteForRole(session.role));
}
