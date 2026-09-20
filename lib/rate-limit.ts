import "server-only";

interface Attempt {
  count: number;
  windowStart: number;
}

const WINDOW_MS = 15 * 60 * 1000; // 15 menit
const MAX_ATTEMPTS = 5;

/**
 * Rate limiter in-memory sederhana (sliding window per kunci — biasanya
 * IP+email) untuk mitigasi brute-force pada endpoint login (Bab K:
 * Keamanan Sisi Klien & Mitigasi OWASP). Pada skala produksi sungguhan
 * ini idealnya dipindah ke penyimpanan bersama (Redis) supaya konsisten
 * lintas instance server — di sini cukup in-memory karena selaras dengan
 * seluruh store lain di proyek ini (reset saat server di-restart).
 */
const attempts = new Map<string, Attempt>();

export interface RateLimitResult {
  allowed: boolean;
  retryAfterSeconds?: number;
}

export function checkRateLimit(key: string): RateLimitResult {
  const now = Date.now();
  const existing = attempts.get(key);

  if (!existing || now - existing.windowStart > WINDOW_MS) {
    attempts.set(key, { count: 1, windowStart: now });
    return { allowed: true };
  }

  if (existing.count >= MAX_ATTEMPTS) {
    const retryAfterSeconds = Math.ceil((existing.windowStart + WINDOW_MS - now) / 1000);
    return { allowed: false, retryAfterSeconds };
  }

  existing.count += 1;
  return { allowed: true };
}

/** Dipanggil setelah login BERHASIL supaya percobaan gagal sebelumnya tidak terus menghukum pengguna sah. */
export function resetRateLimit(key: string): void {
  attempts.delete(key);
}

/** IP klien dari header standar (x-forwarded-for di belakang proxy/edge, x-real-ip sebagai fallback). */
export function getClientIp(request: Request): string {
  const forwardedFor = request.headers.get("x-forwarded-for");
  if (forwardedFor) return forwardedFor.split(",")[0]?.trim() ?? "unknown";
  return request.headers.get("x-real-ip") ?? "unknown";
}
