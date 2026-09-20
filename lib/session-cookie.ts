import "server-only";
import { createHmac, timingSafeEqual } from "node:crypto";

/**
 * Signing cookie sesi (HMAC-SHA256) - Bab K: Keamanan Sisi Klien.
 *
 * Sebelumnya cookie sesi murni JSON.stringify(session) tanpa tanda tangan
 * apa pun — meski httpOnly mencegah akses lewat JavaScript, isinya tetap
 * bisa DIEDIT LANGSUNG lewat tab Application/Storage di DevTools browser
 * (mis. mengubah "role":"perawat" jadi "role":"admin_faskes" untuk eskalasi
 * privilese). Signing menutup celah ini: nilai cookie sekarang berbentuk
 * "<payload base64url>.<tanda tangan HMAC>", dan verifySessionCookie()
 * MENOLAK payload apa pun yang tanda tangannya tidak cocok, sebelum
 * datanya bahkan sempat di-parse sebagai JSON.
 *
 * SESSION_SECRET wajib diset lewat environment variable di lingkungan
 * produksi sungguhan (Vercel/Cloudflare) — TIDAK pernah diberi prefiks
 * NEXT_PUBLIC_ karena harus tetap rahasia di server, tidak boleh ikut
 * masuk ke bundle klien (lihat next.config.ts & README untuk instruksi
 * pengaturan di Vercel).
 */
const FALLBACK_DEV_SECRET = "smarttriage-dev-only-secret-jangan-dipakai-di-produksi";

function getSecret(): string {
  const secret = process.env.SESSION_SECRET;
  if (!secret) {
    if (process.env.NODE_ENV === "production") {
      throw new Error(
        "SESSION_SECRET wajib diset di environment variable pada lingkungan produksi. Lihat README bagian Deployment.",
      );
    }
    return FALLBACK_DEV_SECRET;
  }
  return secret;
}

function sign(payload: string): string {
  return createHmac("sha256", getSecret()).update(payload).digest("base64url");
}

/** Bangun nilai cookie yang sudah ditandatangani dari objek sesi. */
export function signSessionCookie(sessionJson: string): string {
  const payload = Buffer.from(sessionJson, "utf-8").toString("base64url");
  return `${payload}.${sign(payload)}`;
}

/** Verifikasi & buka nilai cookie yang ditandatangani. Mengembalikan null jika tanda tangan tidak cocok / format rusak. */
export function verifySessionCookie(cookieValue: string): string | null {
  const separatorIndex = cookieValue.lastIndexOf(".");
  if (separatorIndex === -1) return null;

  const payload = cookieValue.slice(0, separatorIndex);
  const signature = cookieValue.slice(separatorIndex + 1);
  const expectedSignature = sign(payload);

  const sigBuffer = Buffer.from(signature);
  const expectedBuffer = Buffer.from(expectedSignature);
  // timingSafeEqual mensyaratkan panjang buffer sama; panjang beda berarti pasti tidak cocok.
  if (sigBuffer.length !== expectedBuffer.length || !timingSafeEqual(sigBuffer, expectedBuffer)) {
    return null;
  }

  try {
    return Buffer.from(payload, "base64url").toString("utf-8");
  } catch {
    return null;
  }
}
