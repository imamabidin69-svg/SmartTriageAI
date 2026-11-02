import { screen, waitFor, within } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { describe, expect, it, vi } from "vitest";
import { renderRute } from "@/uji/render";
import { API, KONFIGURASI, problem, REKAP, server } from "@/uji/server";

async function bukaPengaturan() {
  const hasil = renderRute("/pengaturan");
  await screen.findByDisplayValue("smarttriage-rf-v1.0.0");
  return hasil;
}

describe("Pengaturan Triase", () => {
  it("menampilkan konfigurasi tersimpan seperti mockup Gambar 7.2", async () => {
    await bukaPengaturan();
    expect(screen.getByLabelText("Tinggi (menit)")).toHaveValue("10");
    expect(screen.getByLabelText("Ambang kritis (skor)")).toHaveValue("6");
    expect(screen.getByLabelText("Ambang keyakinan")).toHaveValue("0,85");
    expect(await screen.findByDisplayValue("Aktif")).toBeDisabled();
    const rekap = screen.getByRole("complementary");
    expect(await within(rekap).findByText("142")).toBeInTheDocument();
    expect(within(rekap).getByText("(6,3%)")).toBeInTheDocument();
    expect(within(rekap).getByText("9")).toBeInTheDocument();
    expect(within(rekap).getByText("96,4%")).toBeInTheDocument();
  });

  it("hanya mengirim kolom yang berubah", async () => {
    let dikirim: unknown;
    server.use(
      http.patch(`${API}/admin/konfigurasi`, async ({ request }) => {
        dikirim = await request.json();
        return HttpResponse.json({ ...KONFIGURASI, batas_tunggu_sedang: 25, ambang_keyakinan: 0.9 });
      }),
    );
    const { user } = await bukaPengaturan();
    const sedang = screen.getByLabelText("Sedang (menit)");
    await user.clear(sedang);
    await user.type(sedang, "25");
    const keyakinan = screen.getByLabelText("Ambang keyakinan");
    await user.clear(keyakinan);
    await user.type(keyakinan, "0,9");
    await user.click(screen.getByRole("button", { name: "Simpan perubahan" }));
    expect(await screen.findByText("Pengaturan tersimpan dan tercatat di log audit.")).toBeInTheDocument();
    expect(dikirim).toEqual({ batas_tunggu_sedang: 25, ambang_keyakinan: 0.9 });
    expect(screen.getByLabelText("Ambang keyakinan")).toHaveValue("0,9");
  });

  it("tanpa perubahan tidak mengirim apa pun", async () => {
    const patch = vi.fn();
    server.use(http.patch(`${API}/admin/konfigurasi`, patch));
    const { user } = await bukaPengaturan();
    await user.click(screen.getByRole("button", { name: "Simpan perubahan" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Belum ada pengaturan yang diubah.");
    expect(patch).not.toHaveBeenCalled();
  });

  it("memeriksa isian di klien", async () => {
    const { user } = await bukaPengaturan();
    const kritis = screen.getByLabelText("Ambang kritis (skor)");
    await user.clear(kritis);
    await user.type(kritis, "40");
    const keyakinan = screen.getByLabelText("Ambang keyakinan");
    await user.clear(keyakinan);
    await user.type(keyakinan, "abc");
    await user.click(screen.getByRole("button", { name: "Simpan perubahan" }));
    expect(screen.getByText("Ambang kritis maksimal 18.")).toBeInTheDocument();
    expect(screen.getByText("Ambang keyakinan harus berupa angka.")).toBeInTheDocument();
  });

  it("menampilkan pesan urutan ambang dari server di kolomnya", async () => {
    server.use(
      http.patch(`${API}/admin/konfigurasi`, () =>
        problem(422, {
          title: "Data tidak valid",
          detail: "Periksa kembali isian yang ditandai.",
          errors: [{ field: "ambang_tinggi", pesan: "Ambang tinggi harus lebih kecil dari ambang kritis (6)." }],
        }),
      ),
    );
    const { user } = await bukaPengaturan();
    const tinggi = screen.getByLabelText("Ambang tinggi");
    await user.clear(tinggi);
    await user.type(tinggi, "7");
    await user.click(screen.getByRole("button", { name: "Simpan perubahan" }));
    expect(await screen.findByText("Ambang tinggi harus lebih kecil dari ambang kritis (6).")).toBeInTheDocument();
    expect(screen.getByLabelText("Ambang tinggi")).toHaveAttribute("aria-invalid", "true");
  });

  it("pembaca layar tidak aktif dan model triase belum dimuat", async () => {
    server.use(
      http.get(`${API}/health`, () =>
        problem(503, { status: "degraded", komponen: { database: "ok", pembaca_layar: "gagal" } }),
      ),
      http.get(`${API}/admin/konfigurasi`, () => HttpResponse.json({ ...KONFIGURASI, versi_model_termuat: null })),
    );
    await bukaPengaturan();
    expect(await screen.findByDisplayValue("Tidak aktif")).toBeInTheDocument();
    expect(screen.getByText("Kolom hasil pemindaian diisi manual oleh perawat.")).toBeInTheDocument();
    expect(screen.getByText(/tidak ada \(aturan cadangan\)/)).toBeInTheDocument();
  });

  it("mengekspor CSV dari kartu rekap", async () => {
    server.use(
      http.get(`${API}/rekap`, ({ request }) =>
        new URL(request.url).searchParams.get("format") === "csv"
          ? new HttpResponse("a;b", { headers: { "Content-Type": "text/csv" } })
          : problem(500, { title: "Rekap gagal dimuat" }),
      ),
    );
    Object.assign(URL, { createObjectURL: () => "blob:x", revokeObjectURL: () => undefined });
    const klik = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);
    const { user } = await bukaPengaturan();
    expect(await screen.findByText("Rekap gagal dimuat")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Ekspor CSV" }));
    await waitFor(() => expect(klik).toHaveBeenCalled());
  });

  it("ekspor yang gagal ditampilkan sebagai notifikasi", async () => {
    server.use(
      http.get(`${API}/rekap`, ({ request }) =>
        new URL(request.url).searchParams.get("format") === "csv"
          ? problem(500, { title: "Ekspor gagal" })
          : HttpResponse.json(REKAP),
      ),
    );
    const { user } = await bukaPengaturan();
    await user.click(await screen.findByRole("button", { name: "Ekspor CSV" }));
    expect(await screen.findByText("Ekspor gagal")).toBeInTheDocument();
  });

  it("gagal memuat konfigurasi", async () => {
    server.use(http.get(`${API}/admin/konfigurasi`, () => problem(500, { title: "Konfigurasi gagal dimuat" })));
    renderRute("/pengaturan");
    expect(await screen.findByText("Konfigurasi gagal dimuat")).toBeInTheDocument();
  });
});
