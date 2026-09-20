import "server-only";
import { randomBytes, scryptSync, timingSafeEqual } from "node:crypto";

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

  if (storedBuffer.length !== suppliedBuffer.length) return false;
  return timingSafeEqual(storedBuffer, suppliedBuffer);
}
