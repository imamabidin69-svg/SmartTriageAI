import "server-only";
import { randomBytes, scryptSync, timingSafeEqual } from "node:crypto";

/**
 * Hashing password dengan scrypt (modul bawaan Node.js, bukan pustaka
 * eksternal) - scrypt adalah Key Derivation Function yang memang dirancang
 * tahan brute-force (mahal secara komputasi & memori), setara secara
 * prinsip dengan bcrypt/argon2 yang lebih populer di dunia Node, tapi tanpa
 * perlu menambah dependency native (bcrypt punya native binding yang kadang
 * rewel di lingkungan Windows).
 *
 * Format penyimpanan: "salt:hash" (keduanya hex), digabung satu string
 * supaya gampang disimpan sebagai satu kolom passwordHash.
 */
const KEY_LENGTH = 64;

export function hashPassword(password: string): string {
  const salt = randomBytes(16).toString("hex");
  const derivedKey = scryptSync(password, salt, KEY_LENGTH);
  return `${salt}:${derivedKey.toString("hex")}`;
}

export function verifyPassword(password: string, storedHash: string): boolean {
  const [salt, hashHex] = storedHash.split(":");
  if (!salt || !hashHex) return false;

  const storedBuffer = Buffer.from(hashHex, "hex");
  const suppliedBuffer = scryptSync(password, salt, KEY_LENGTH);

  // timingSafeEqual mencegah timing attack (menebak password dari selisih
  // waktu perbandingan byte-per-byte); kedua buffer WAJIB sama panjang dulu
  // sebelum dibandingkan, atau fungsi ini melempar error.
  if (storedBuffer.length !== suppliedBuffer.length) return false;
  return timingSafeEqual(storedBuffer, suppliedBuffer);
}
