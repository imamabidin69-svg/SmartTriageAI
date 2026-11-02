import { describe, expect, it } from "vitest";
import { ProblemError } from "@/api/klien";
import { bolehUlang } from "./App";

describe("bolehUlang", () => {
  it("error 4xx tidak diulang, gangguan server diulang sekali", () => {
    expect(bolehUlang(0, new ProblemError(404, {}))).toBe(false);
    expect(bolehUlang(0, new ProblemError(503, {}))).toBe(true);
    expect(bolehUlang(1, new ProblemError(0, {}))).toBe(false);
  });
});
