/**
 * Query key builders - sengaja dipisah dari hooks/useTriaseQueries.ts (yang
 * ber-"use client") karena directive "use client" menandai SELURUH modul
 * sebagai boundary klien, termasuk fungsi murni non-hook seperti ini. Server
 * Component (mis. app/(protected)/dashboard/page.tsx) perlu queryKey yang
 * SAMA PERSIS dengan yang dipakai Client Component saat prefetchQuery, jadi
 * key builder harus tinggal di modul netral tanpa batasan client/server.
 */
export const antreanKey = () => ["antrean"] as const;
export const triaseDetailKey = (idTriase: string) => ["triase", idTriase] as const;
export const staffKey = () => ["staff"] as const;
export const passwordResetsKey = () => ["password-resets"] as const;
export const pasienKey = () => ["pasien"] as const;
