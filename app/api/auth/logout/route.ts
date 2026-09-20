import { NextResponse } from "next/server";
import { SESSION_COOKIE } from "@/lib/constants";

/** POST /api/auth/logout - menghapus cookie sesi. */
export async function POST() {
  const response = NextResponse.json({ ok: true });
  response.cookies.delete(SESSION_COOKIE);
  return response;
}
