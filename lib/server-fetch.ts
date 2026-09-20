import "server-only";
import { cookies, headers } from "next/headers";

export async function serverFetch(path: string, init?: RequestInit): Promise<Response> {
  const hdrs = await headers();
  const host = hdrs.get("host") ?? "localhost:3000";
  const protocol = hdrs.get("x-forwarded-proto") ?? (host.includes("localhost") ? "http" : "https");
  const cookieStore = await cookies();

  return fetch(`${protocol}://${host}${path}`, {
    ...init,
    headers: {
      ...(init?.headers ?? {}),
      cookie: cookieStore.toString(),
    },
    cache: "no-store",
  });
}
