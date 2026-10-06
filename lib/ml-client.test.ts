import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { Pasien } from "@/lib/schemas/pasien.schema";
import type { TriageInput } from "@/lib/schemas/triase.schema";

const { getPasienByIdMock } = vi.hoisted(() => ({ getPasienByIdMock: vi.fn() }));
vi.mock("@/lib/data/pasien-store", () => ({ getPasienById: getPasienByIdMock }));

// classify() dari lib/classify.ts SENGAJA TIDAK di-mock: fungsi itu murni
// (deterministik dari input + konfigurasi ambang bawaan), jadi test di sini
// sekalian memverifikasi fallback benar-benar menghasilkan risk level yang
// masuk akal, bukan cuma "dipanggil".
const { hitungUsia, classifyWithMl } = await import("@/lib/ml-client");

function buatInput(override: Partial<TriageInput> = {}): TriageInput {
  return {
    idPasien: "a1a1a1a1-0001-4000-8000-000000000001",
    namaPasien: "Pasien Uji",
    gejala: "Nyeri dada menjalar ke lengan kiri, sesak napas mendadak.",
    keluhanUtama: "Nyeri dada hebat",
    tandaVital: {
      tekananDarahSistolik: 168,
      tekananDarahDiastolik: 102,
      suhuTubuh: 37.1,
      nadiPerMenit: 118,
      lajuNapas: 28,
      saturasiOksigen: 91,
    },
    ...override,
  };
}

function buatPasien(override: Partial<Pasien> = {}): Pasien {
  return {
    id: "a1a1a1a1-0001-4000-8000-000000000001",
    nama: "Pasien Uji",
    faskesId: "c0000000-0000-4000-8000-000000000001",
    didaftarkanOlehUserId: "d0000000-0000-4000-8000-000000000001",
    didaftarkanOlehNama: "Petugas Uji",
    waktuDaftar: new Date().toISOString(),
    ...override,
  };
}

describe("hitungUsia", () => {
  it("mengembalikan null kalau tanggal lahir tidak ada", () => {
    expect(hitungUsia(undefined)).toBeNull();
  });

  it("mengembalikan null kalau tanggal lahir tidak valid", () => {
    expect(hitungUsia("bukan-tanggal")).toBeNull();
  });

  it("menghitung usia dengan benar kalau ulang tahun sudah lewat tahun ini", () => {
    const sekarang = new Date();
    const lahir = new Date(sekarang.getFullYear() - 30, sekarang.getMonth() - 1, 1);
    expect(hitungUsia(lahir.toISOString().slice(0, 10))).toBe(30);
  });

  it("mengurangi 1 tahun kalau ulang tahun belum lewat tahun ini", () => {
    const sekarang = new Date();
    // bulan depan (modulo 12) -> ulang tahun belum lewat, usia sebenarnya masih tahun-31
    const bulanDepan = (sekarang.getMonth() + 1) % 12;
    const lahir = new Date(sekarang.getFullYear() - 30, bulanDepan, 15);
    if (lahir > sekarang) lahir.setFullYear(lahir.getFullYear() - 1);
    const hasil = hitungUsia(lahir.toISOString().slice(0, 10));
    expect(hasil).not.toBeNull();
    expect(hasil).toBeGreaterThanOrEqual(28);
    expect(hasil).toBeLessThanOrEqual(30);
  });
});

describe("classifyWithMl", () => {
  const ML_URL = "http://ml-service.test";
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    getPasienByIdMock.mockReset();
    fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
  });

  it("jatuh ke classify() kalau ML_SERVICE_URL belum diatur", async () => {
    vi.stubEnv("ML_SERVICE_URL", "");
    const hasil = await classifyWithMl(buatInput());
    expect(hasil.sumber).toBe("aturan");
    expect(hasil.riskLevel).toBe("kritis"); // sesuai contoh nyata di lib/data/triase-store.ts
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("memakai hasil layanan ML kalau respons sukses dan lengkap", async () => {
    vi.stubEnv("ML_SERVICE_URL", ML_URL);
    getPasienByIdMock.mockReturnValue(buatPasien({ tanggalLahir: "1985-04-12", jenisKelamin: "laki_laki" }));
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({
        riskLevel: "tinggi",
        probabilitas: { rendah: 0.1, sedang: 0.2, tinggi: 0.5, kritis: 0.2 },
        penjelasanAi: "Model machine learning merekomendasikan risk level TINGGI.",
        faktorUtama: ["saturasi oksigen"],
        modelVersion: "smarttriage-rf-v1.0.0",
      }),
    });

    const hasil = await classifyWithMl(buatInput());

    expect(hasil).toEqual({
      riskLevel: "tinggi",
      penjelasanAi: "Model machine learning merekomendasikan risk level TINGGI.",
      sumber: "ml",
    });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const panggilan = fetchMock.mock.calls[0];
    if (!panggilan) throw new Error("fetch tidak terpanggil");
    const [url, opsi] = panggilan;
    expect(url).toBe(`${ML_URL}/classify`);
    const body = JSON.parse(opsi.body as string);
    expect(body).toMatchObject({ SBP: 168, DBP: 102, HR: 118, RR: 28, BT: 37.1, Saturation: 91, Sex: 2 });
  });

  it("memetakan tingkatKesadaran dan skalaNyeri ke kode yang benar untuk layanan ML", async () => {
    vi.stubEnv("ML_SERVICE_URL", ML_URL);
    getPasienByIdMock.mockReturnValue(buatPasien({ jenisKelamin: "perempuan" }));
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ riskLevel: "sedang", penjelasanAi: "ok" }),
    });

    await classifyWithMl(buatInput({ tingkatKesadaran: "respons_nyeri", skalaNyeri: 7 }));

    const body = JSON.parse(fetchMock.mock.calls[0]?.[1].body as string);
    expect(body.Mental).toBe(3); // respons_nyeri -> kode 3
    expect(body.NRS_pain).toBe(7);
    expect(body.Sex).toBe(1); // perempuan -> 1
  });

  it("jatuh ke classify() kalau layanan ML mengembalikan status bukan 2xx", async () => {
    vi.stubEnv("ML_SERVICE_URL", ML_URL);
    getPasienByIdMock.mockReturnValue(null);
    fetchMock.mockResolvedValue({ ok: false, status: 500, json: async () => ({}) });

    const hasil = await classifyWithMl(buatInput());
    expect(hasil.sumber).toBe("aturan");
  });

  it("jatuh ke classify() kalau respons ML tidak lengkap (riskLevel/penjelasanAi kosong)", async () => {
    vi.stubEnv("ML_SERVICE_URL", ML_URL);
    getPasienByIdMock.mockReturnValue(null);
    fetchMock.mockResolvedValue({ ok: true, json: async () => ({ riskLevel: "tinggi" }) }); // penjelasanAi hilang

    const hasil = await classifyWithMl(buatInput());
    expect(hasil.sumber).toBe("aturan");
  });

  it("jatuh ke classify() kalau fetch gagal (network error/timeout)", async () => {
    vi.stubEnv("ML_SERVICE_URL", ML_URL);
    getPasienByIdMock.mockReturnValue(null);
    fetchMock.mockRejectedValue(new Error("fetch failed"));

    const hasil = await classifyWithMl(buatInput());
    expect(hasil.sumber).toBe("aturan");
    expect(hasil.riskLevel).toBeDefined();
  });

  it("tetap jalan kalau data pasien tidak ditemukan (usia/jenis kelamin null)", async () => {
    vi.stubEnv("ML_SERVICE_URL", ML_URL);
    getPasienByIdMock.mockReturnValue(null);
    fetchMock.mockResolvedValue({ ok: true, json: async () => ({ riskLevel: "rendah", penjelasanAi: "ok" }) });

    await classifyWithMl(buatInput());

    const body = JSON.parse(fetchMock.mock.calls[0]?.[1].body as string);
    expect(body.Age).toBeNull();
    expect(body.Sex).toBeNull();
  });
});
