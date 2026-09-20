import "server-only";
import { cookies, headers } from "next/headers";

/**
 * serverFetch() - dipakai Server Component/generateMetadata untuk memanggil
 * Route Handler MILIK APLIKASI SENDIRI lewat HTTP sungguhan.
 *
 * KENAPA TIDAK IMPOR LANGSUNG lib/data/triase-store.ts DI SINI?
 * Next.js App Router mengompilasi Route Handler (route.ts) dan React Server
 * Component (page.tsx/generateMetadata) sebagai TARGET BUNDLING YANG
 * TERPISAH — walau keduanya berjalan dalam proses `next start` yang sama,
 * Next.js TIDAK MENJAMIN modul-level state (seperti array in-memory di
 * triase-store.ts) dibagikan di antara keduanya. Ini sempat menyebabkan bug
 * nyata saat pengujian: data yang baru disimpan lewat POST /api/triase
 * tidak terlihat oleh generateMetadata di halaman detail.
 *
 * Solusinya: SEMUA pembaca data — baik Client Component (via
 * lib/api-client.ts) maupun Server Component (via file ini) — wajib lewat
 * Route Handler yang sama sebagai satu-satunya sumber kebenaran. Pola ini
 * juga persis meniru bagaimana Server Component akan bicara ke backend
 * sungguhan (REST API terpisah) pada implementasi produksi (SKPL Bab V).
 */
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
