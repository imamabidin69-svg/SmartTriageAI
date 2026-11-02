import { screen, waitFor } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { describe, expect, it, vi } from "vitest";
import { renderRute } from "@/uji/render";
import { API, problem, REKAP, server } from "@/uji/server";
import { periksaRentang } from "./Rekap";

describe("periksaRentang", () => {
  it("sama dengan aturan rentang di backend", () => {
    expect(periksaRentang("", "2026-10-17")).toBe("Isi tanggal awal dan tanggal akhir.");
    expect(periksaRentang("2026-10-18", "2026-10-17")).toBe("Tanggal awal tidak boleh melewati tanggal akhir.");
    expect(periksaRentang("2025-01-01", "2026-01-02")).toBe("Rentang tanggal maksimal 366 hari.");
    expect(periksaRentang("2025-01-02", "2026-01-02")).toBeUndefined();
  });
});

describe("Halaman Rekap", () => {
  it("menampilkan ringkasan dan tabel per level", async () => {
    renderRute("/rekap");
    expect(await screen.findByText("142")).toBeInTheDocument();
    expect(screen.getByText("6,3%")).toBeInTheDocument();
    expect(screen.getByText("17")).toBeInTheDocument();
    expect(screen.getByText("25,4 menit")).toBeInTheDocument();
    expect(screen.getByText("Periode 11 Okt 2026 sampai 17 Okt 2026")).toBeInTheDocument();
    expect(screen.getAllByRole("row")).toHaveLength(5);
  });

  it("memuat rentang baru dan menolak rentang terbalik", async () => {
    const diminta: string[] = [];
    server.use(
      http.get(`${API}/rekap`, ({ request }) => {
        diminta.push(new URL(request.url).search);
        return HttpResponse.json({ ...REKAP, akurasi_pemindaian: null });
      }),
    );
    const { user } = renderRute("/rekap");
    await screen.findByText("142");
    expect(screen.getByText("Belum ada pemindaian yang dikonfirmasi")).toBeInTheDocument();
    // Tanggal akhir diisi sendiri supaya tes tidak bergantung pada tanggal hari ini.
    const sampai = screen.getByLabelText("Sampai tanggal");
    await user.clear(sampai);
    await user.type(sampai, "2026-10-17");
    const dari = screen.getByLabelText("Dari tanggal");
    await user.clear(dari);
    await user.type(dari, "2026-10-18");
    await user.click(screen.getByRole("button", { name: "Tampilkan rekap" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Tanggal awal tidak boleh melewati tanggal akhir.");
    await user.clear(dari);
    await user.type(dari, "2026-10-01");
    await user.click(screen.getByRole("button", { name: "Tampilkan rekap" }));
    await waitFor(() => expect(diminta.at(-1)).toContain("dari=2026-10-01&sampai=2026-10-17"));
  });

  it("mengekspor CSV dengan rentang yang sama", async () => {
    let alamat = "";
    server.use(
      http.get(`${API}/rekap`, ({ request }) => {
        const url = new URL(request.url);
        if (url.searchParams.get("format") !== "csv") return HttpResponse.json(REKAP);
        alamat = url.search;
        return new HttpResponse("x", { headers: { "Content-Type": "text/csv" } });
      }),
    );
    Object.assign(URL, { createObjectURL: () => "blob:x", revokeObjectURL: () => undefined });
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);
    const { user } = renderRute("/rekap");
    await screen.findByText("142");
    await user.click(screen.getByRole("button", { name: "Ekspor CSV" }));
    await waitFor(() => expect(alamat).toContain("format=csv"));
    expect(alamat).toContain("dari=");
  });

  it("ekspor dan pemuatan yang gagal", async () => {
    server.use(http.get(`${API}/rekap`, () => problem(500, { title: "Rekap gagal dimuat" })));
    renderRute("/rekap");
    expect(await screen.findByRole("alert")).toHaveTextContent("Rekap gagal dimuat");
  });

  it("notifikasi saat ekspor gagal", async () => {
    server.use(
      http.get(`${API}/rekap`, ({ request }) =>
        new URL(request.url).searchParams.get("format") === "csv"
          ? problem(500, { title: "Ekspor gagal" })
          : HttpResponse.json(REKAP),
      ),
    );
    const { user } = renderRute("/rekap");
    await screen.findByText("142");
    await user.click(screen.getByRole("button", { name: "Ekspor CSV" }));
    expect(await screen.findByText("Ekspor gagal")).toBeInTheDocument();
  });
});
