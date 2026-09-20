import "server-only";
import { createHmac, timingSafeEqual } from "node:crypto";

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

export function signSessionCookie(sessionJson: string): string {
  const payload = Buffer.from(sessionJson, "utf-8").toString("base64url");
  return `${payload}.${sign(payload)}`;
}

export function verifySessionCookie(cookieValue: string): string | null {
  const separatorIndex = cookieValue.lastIndexOf(".");
  if (separatorIndex === -1) return null;

  const payload = cookieValue.slice(0, separatorIndex);
  const signature = cookieValue.slice(separatorIndex + 1);
  const expectedSignature = sign(payload);

  const sigBuffer = Buffer.from(signature);
  const expectedBuffer = Buffer.from(expectedSignature);
  if (sigBuffer.length !== expectedBuffer.length || !timingSafeEqual(sigBuffer, expectedBuffer)) {
    return null;
  }

  try {
    return Buffer.from(payload, "base64url").toString("utf-8");
  } catch {
    return null;
  }
}
