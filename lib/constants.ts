/** Nama cookie sesi. Dipisah ke file sendiri (tanpa dependency next/headers)
 * agar bisa diimpor baik oleh middleware.ts (Edge Runtime, pakai
 * request.cookies) maupun lib/session.ts (Node runtime, pakai next/headers). */
export const SESSION_COOKIE = "smarttriage_session";
