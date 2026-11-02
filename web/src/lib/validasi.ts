import type { ZodError } from "zod";

/** Pesan pertama per field dari hasil validasi Zod, dalam bentuk yang sama dengan pesanField ProblemError. */
export function galatZod(galat: ZodError): Record<string, string> {
  const hasil: Record<string, string> = {};
  for (const isu of galat.issues) {
    const field = String(isu.path[0] ?? "body");
    hasil[field] ??= isu.message;
  }
  return hasil;
}
