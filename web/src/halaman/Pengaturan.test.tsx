import { screen, waitFor, within } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { describe, expect, it, vi } from "vitest";
import { renderRute } from "@/uji/render";
import { API, KONFIGURASI, problem, REKAP, server } from "@/uji/server";

async function bukaPengaturan() {
  const hasil = renderRute("/pengaturan");
  await screen.findByDisplayValue("rf-icu-physionet2019-v1");
  return hasil;
}

describe("Pengaturan Penilaian ICU", () => {
  it("menampilkan konfigurasi tersimpan seperti mockup Gambar 7.2", async () => {
    await bukaPengaturan();
    expect(screen.getByLabelText("Kritis (menit)")).toHaveValue("15");
    expect(screen.getByLabelText("Tinggi (menit)")).toHaveValue("30");
    expect(screen.getByLabelText("Rendah (menit)")).toHaveValue("120");
    expect(screen.getByLabelText("Kritis (skor)")).toHaveValue("7");
    expect(screen.getByLabelText("Sedang (skor)")).toHaveValue("3");
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
    const kritis = screen.getByLabelText("Kritis (skor)");
    await user.clear(kritis);
    await user.type(kritis, "40");
    const intervalKritis = screen.getByLabelText("Kritis (menit)");
    await user.clear(intervalKritis);
    const keyakinan = screen.getByLabelText("Ambang keyakinan");
    await user.clear(keyakinan);
    await user.type(keyakinan, "abc");
    await user.click(screen.getByRole("button", { name: "Simpan perubahan" }));
    expect(screen.getByText("Ambang kritis maksimal 20.")).toBeInTheDocument();
    expect(screen.getByText("Interval kritis minimal 1.")).toBeInTheDocument();
    expect(screen.getByText("Ambang keyakinan harus berupa angka.")).toBeInTheDocument();
  });

  it("menampilkan pesan urutan ambang dari server di kolomnya", async () => {
    server.use(
      http.patch(`${API}/admin/konfigurasi`, () =>
        problem(422, {
          title: "Data tidak valid",
          detail: "Periksa kembali isian yang ditandai.",
          errors: [
            { field: "ambang_tinggi", pesan: "Ambang NEWS2 tinggi harus lebih kecil dari ambang NEWS2 kritis (7)." },
          ],
        }),
      ),
    );
    const { user } = await bukaPengaturan();
    const tinggi = screen.getByLabelText("Tinggi (skor)");
    await user.clear(tinggi);
    await user.type(tinggi, "8");
    await user.click(screen.getByRole("button", { name: "Simpan perubahan" }));
    expect(
      await screen.findByText("Ambang NEWS2 tinggi harus lebih kecil dari ambang NEWS2 kritis (7)."),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Tinggi (skor)")).toHaveAttribute("aria-invalid", "true");
  });

  it("pembaca layar tidak aktif dan model perburukan belum dimuat", async () => {
    server.use(
      http.get(`${API}/health`, () =>
        problem(503, { status: "degraded", komponen: { database: "ok", pembaca_layar: "gagal" } }),
      ),
      http.get(`${API}/admin/konfigurasi`, () => HttpResponse.json({ ...KONFIGURASI, versi_model_termuat: null })),
    );
    await bukaPengaturan();
    expect(await screen.findByDisplayValue("Tidak aktif")).toBeInTheDocument();
    expect(screen.getByText("Kolom hasil pemindaian diisi manual oleh perawat.")).toBeInTheDocument();
    expect(screen.getByText(/tidak ada \(NEWS2 saja\)/)).toBeInTheDocument();
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
