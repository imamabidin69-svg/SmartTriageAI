import { HttpResponse, http } from "msw";
import { describe, expect, it, vi } from "vitest";
import { aturCookie } from "@/uji/cookie";
import { API, problem, server } from "@/uji/server";
import { bacaCookie, ProblemError, perbaruiToken, permintaan, pesanError, susunAlamat, TIPE, unduh } from "./klien";

async function gagal(janji: Promise<unknown>): Promise<ProblemError> {
  const hasil = await janji.catch((e: unknown) => e);
  if (!(hasil instanceof ProblemError)) throw new Error("seharusnya ProblemError");
  return hasil;
}

describe("susunAlamat", () => {
  it("membuang parameter kosong", () => {
    expect(susunAlamat("/rekap", { dari: "2026-10-01", sampai: undefined, aksi: "", ukuran: 50, x: null })).toBe(
      "/api/v1/rekap?dari=2026-10-01&ukuran=50",
    );
    expect(susunAlamat("/auth/me")).toBe("/api/v1/auth/me");
  });
});

describe("permintaan", () => {
  it("mengirim CSRF dari cookie untuk request yang mengubah data", async () => {
    aturCookie("csrf_access_token", "abc123");
    aturCookie("csrf_refresh_token", "ref456");
    const diterima: Record<string, string | null> = {};
    server.use(
      http.patch(`${API}/admin/konfigurasi`, ({ request }) => {
        diterima.access = request.headers.get("X-CSRF-TOKEN");
        return HttpResponse.json({ ok: true });
      }),
      http.post(`${API}/auth/logout`, ({ request }) => {
        diterima.refresh = request.headers.get("X-CSRF-TOKEN");
        return new HttpResponse(null, { status: 204 });
      }),
    );
    expect(await permintaan("/admin/konfigurasi", { method: "PATCH", json: { ambang_kritis: 7 } })).toEqual({
      ok: true,
    });
    expect(await permintaan("/auth/logout", { method: "POST", csrf: "refresh" })).toBeUndefined();
    expect(diterima).toEqual({ access: "abc123", refresh: "ref456" });
  });

  it("mengubah Problem Details menjadi ProblemError dengan pesan per field", async () => {
    server.use(
      http.post(`${API}/admin/staf`, () =>
        problem(422, {
          type: TIPE.VALIDASI,
          title: "Data tidak valid",
          errors: [{ field: "email", pesan: "Format email tidak valid." }],
        }),
      ),
    );
    const galat = await gagal(permintaan("/admin/staf", { method: "POST", json: {} }));
    expect(galat.status).toBe(422);
    expect(galat.pesanField).toEqual({ email: "Format email tidak valid." });
    expect(pesanError(galat)).toBe("Data tidak valid");
  });

  it("membaca Retry-After dan isi yang bukan JSON", async () => {
    server.use(
      http.get(`${API}/rekap`, () => problem(429, { detail: "Terlalu cepat." }, { "Retry-After": "30" })),
      http.get(`${API}/health`, () => new HttpResponse("bukan json", { status: 502 })),
    );
    const terlalu = await gagal(permintaan("/rekap"));
    expect(terlalu.cobaLagiDetik).toBe(30);
    expect(pesanError(terlalu)).toBe("Terlalu cepat.");
    const rusak = await gagal(permintaan("/health"));
    expect(rusak.status).toBe(502);
    expect(rusak.judul).toBe("Terjadi kesalahan pada server");
  });

  it("memperbarui token yang kedaluwarsa lalu mengulang request sekali", async () => {
    let panggilan = 0;
    let refresh = 0;
    server.use(
      http.get(`${API}/admin/staf`, () => {
        panggilan += 1;
        return panggilan === 1
          ? problem(401, { type: TIPE.TOKEN_KEDALUWARSA, title: "Token kedaluwarsa" })
          : HttpResponse.json({ items: [] });
      }),
      http.post(`${API}/auth/refresh`, () => {
        refresh += 1;
        return HttpResponse.json({ pengguna: {} });
      }),
    );
    expect(await permintaan("/admin/staf")).toEqual({ items: [] });
    expect([panggilan, refresh]).toEqual([2, 1]);
  });

  it("cookie access yang sudah dibuang peramban tetap diperbarui selama cookie refresh ada", async () => {
    let panggilan = 0;
    server.use(
      http.get(`${API}/auth/me`, () => {
        panggilan += 1;
        return panggilan === 1
          ? problem(401, { type: TIPE.TIDAK_TERAUTENTIKASI, title: "Belum masuk" })
          : HttpResponse.json({ nama: "Admin" });
      }),
      http.post(`${API}/auth/refresh`, () => HttpResponse.json({})),
    );
    expect(await gagal(permintaan("/auth/me")).then((g) => g.status)).toBe(401);
    aturCookie("csrf_refresh_token", "ref456");
    panggilan = 0;
    expect(await permintaan("/auth/me")).toEqual({ nama: "Admin" });
  });

  it("refresh yang gagal meneruskan error 401", async () => {
    server.use(
      http.get(`${API}/admin/staf`, () => problem(401, { type: TIPE.TOKEN_KEDALUWARSA, title: "Token kedaluwarsa" })),
      http.post(`${API}/auth/refresh`, () => problem(401, { title: "Sesi berakhir" })),
    );
    const galat = await gagal(permintaan("/admin/staf"));
    expect(galat.status).toBe(401);
  });

  it("beberapa request bersamaan hanya memicu satu refresh", async () => {
    let refresh = 0;
    server.use(
      http.post(`${API}/auth/refresh`, async () => {
        refresh += 1;
        return HttpResponse.json({});
      }),
    );
    await Promise.all([perbaruiToken(), perbaruiToken()]);
    expect(refresh).toBe(1);
  });

  it("gangguan jaringan menjadi pesan yang jelas", async () => {
    server.use(http.get(`${API}/auth/me`, () => HttpResponse.error()));
    const galat = await gagal(permintaan("/auth/me"));
    expect(galat.status).toBe(0);
    expect(pesanError(galat)).toContain("Server tidak dapat dihubungi");
    expect(pesanError(new Error("x"))).toBe("Terjadi kesalahan. Coba lagi beberapa saat lagi.");
  });

  it("membaca cookie yang tidak ada", () => {
    expect(bacaCookie("tidak_ada")).toBeUndefined();
  });
});

describe("unduh", () => {
  it("memakai nama berkas dari Content-Disposition", async () => {
    server.use(
      http.get(
        `${API}/rekap`,
        () =>
          new HttpResponse("a;b\n1;2", {
            headers: { "Content-Type": "text/csv", "Content-Disposition": 'attachment; filename="rekap-2026.csv"' },
          }),
      ),
    );
    const buat = vi.fn(() => "blob:rekap");
    const lepas = vi.fn();
    Object.assign(URL, { createObjectURL: buat, revokeObjectURL: lepas });
    const klik = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);
    expect(await unduh("/rekap", { format: "csv" }, "cadangan.csv")).toBe("rekap-2026.csv");
    expect(klik).toHaveBeenCalled();
    expect(lepas).toHaveBeenCalledWith("blob:rekap");
  });

  it("memakai nama cadangan bila server tidak memberi nama", async () => {
    server.use(http.get(`${API}/rekap`, () => new HttpResponse("x", { headers: { "Content-Type": "text/csv" } })));
    Object.assign(URL, { createObjectURL: () => "blob:x", revokeObjectURL: () => undefined });
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);
    expect(await unduh("/rekap", {}, "cadangan.csv")).toBe("cadangan.csv");
  });
});
