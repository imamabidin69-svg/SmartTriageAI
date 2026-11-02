import { describe, expect, it, vi } from "vitest";
import { z } from "zod";
import { angka, persen, selisihHari, tanggal, tanggalWib, waktuWib } from "./format";
import { useNotifikasi } from "./notifikasi";
import { bacaSesi, bacaTautan, simpanSesi, simpanTautan, tokenDariFragmen } from "./sesiEir";
import { galatZod } from "./validasi";

describe("format", () => {
  it("menulis waktu dalam WIB", () => {
    expect(waktuWib("2026-10-17T03:05:00+00:00")).toMatch(/17 Okt 2026.*10[.:]05 WIB/);
    expect(tanggal("2026-10-17")).toBe("17 Okt 2026");
    expect(tanggal("2026-10-16T20:00:00+00:00")).toBe("17 Okt 2026");
  });

  it("menghitung tanggal WIB walau UTC masih hari sebelumnya", () => {
    const pukul2DiniHariWib = new Date("2026-10-16T19:00:00Z");
    expect(tanggalWib(0, pukul2DiniHariWib)).toBe("2026-10-17");
    expect(tanggalWib(-6, pukul2DiniHariWib)).toBe("2026-10-11");
  });

  it("menulis angka gaya Indonesia", () => {
    expect(angka(1234.5, 1)).toBe("1.234,5");
    expect(persen(96.44)).toBe("96,4%");
    expect(persen(null)).toBe("-");
    expect(selisihHari("2026-01-01", "2026-12-31")).toBe(364);
  });
});

describe("validasi", () => {
  it("mengambil pesan pertama per field", () => {
    const hasil = z
      .object({ a: z.string().min(2, "Pendek").email("Bukan email"), b: z.string() })
      .safeParse({ a: "x", b: 1 });
    expect(hasil.success).toBe(false);
    if (!hasil.success) expect(galatZod(hasil.error)).toEqual({ a: "Pendek", b: "Expected string, received number" });
  });
});

describe("notifikasi", () => {
  it("menambah dan menutup notifikasi", () => {
    useNotifikasi.getState().tampilkan("Tersimpan");
    useNotifikasi.getState().tampilkan("Gagal", "galat");
    const [satu, dua] = useNotifikasi.getState().daftar;
    expect([satu?.jenis, dua?.jenis]).toEqual(["sukses", "galat"]);
    useNotifikasi.getState().tutup(satu?.id ?? 0);
    expect(useNotifikasi.getState().daftar.map((n) => n.pesan)).toEqual(["Gagal"]);
  });
});

describe("sesiEir", () => {
  const sesi = {
    idSesi: "s1",
    tokenSesi: "tok",
    kedaluwarsa: "2026-10-17T05:00:00Z",
    pesan: [],
    status: "berjalan" as const,
    bolehSelesai: false,
    jumlahJawaban: 0,
  };

  it("membaca token dari fragmen alamat", () => {
    expect(tokenDariFragmen("#t=abc.def")).toBe("abc.def");
    expect(tokenDariFragmen("#x=1")).toBeUndefined();
    expect(tokenDariFragmen("")).toBeUndefined();
  });

  it("menyimpan tautan dan sesi, serta membuang sesi kedaluwarsa", () => {
    simpanTautan("tok-tautan");
    expect(bacaTautan()).toBe("tok-tautan");
    simpanTautan(null);
    expect(bacaTautan()).toBeUndefined();

    simpanSesi(sesi);
    expect(bacaSesi(new Date("2026-10-17T04:00:00Z"))).toEqual(sesi);
    expect(bacaSesi(new Date("2026-10-17T06:00:00Z"))).toBeUndefined();
    simpanSesi(null);
    expect(bacaSesi()).toBeUndefined();
  });

  it("isi penyimpanan yang rusak diabaikan", () => {
    sessionStorage.setItem("eir-sesi", "{rusak");
    expect(bacaSesi()).toBeUndefined();
    sessionStorage.setItem("eir-sesi", JSON.stringify({ idSesi: "" }));
    expect(bacaSesi()).toBeUndefined();
  });

  it("penyimpanan yang diblokir tidak menghentikan halaman", () => {
    const diblokir = () => {
      throw new Error("diblokir");
    };
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(diblokir);
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(diblokir);
    expect(bacaTautan()).toBeUndefined();
    expect(() => simpanTautan("x")).not.toThrow();
  });
});
