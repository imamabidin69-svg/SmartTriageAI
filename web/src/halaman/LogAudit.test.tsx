import { screen, waitFor } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";
import type { ItemLogAudit } from "@/api/tipe";
import { renderRute } from "@/uji/render";
import { ADMIN, API, DAFTAR_STAF, problem, server } from "@/uji/server";

const KOREKSI: ItemLogAudit = {
  id_log: "10000000-0000-4000-8000-000000000001",
  waktu: "2026-10-17T03:05:00+00:00",
  aksi: "koreksi",
  aktor: { id_pengguna: "c0000000-0000-4000-8000-000000000003", nama: "Budi Dokter" },
  id_triase: "20000000-0000-4000-8000-000000000001",
  level_sebelum: "sedang",
  level_sesudah: "tinggi",
  catatan: "Nyeri dada bertambah saat diperiksa",
};

const UBAH_KONFIG: ItemLogAudit = {
  id_log: "10000000-0000-4000-8000-000000000002",
  waktu: "2026-10-16T03:05:00+00:00",
  aksi: "ubah_konfigurasi",
  aktor: { id_pengguna: ADMIN.id_pengguna, nama: ADMIN.nama },
  id_triase: null,
  level_sebelum: null,
  level_sesudah: null,
  catatan: null,
};

describe("Log Audit", () => {
  it("menampilkan catatan, memuat halaman berikutnya, dan menyaring", async () => {
    const diminta: URLSearchParams[] = [];
    server.use(
      http.get(`${API}/admin/log-audit`, ({ request }) => {
        const params = new URL(request.url).searchParams;
        diminta.push(params);
        if (params.get("kursor") === "k2") return HttpResponse.json({ items: [UBAH_KONFIG], kursor_berikutnya: null });
        return HttpResponse.json({ items: [KOREKSI], kursor_berikutnya: "k2" });
      }),
    );
    const { user } = renderRute("/log-audit");
    expect(await screen.findByText("Nyeri dada bertambah saat diperiksa")).toBeInTheDocument();
    expect(screen.getByRole("cell", { name: "Mengoreksi risk level" })).toBeInTheDocument();
    expect(screen.getByText("Sedang")).toBeInTheDocument();
    expect(screen.getByText(/17 Okt 2026.*WIB/)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Muat catatan sebelumnya" }));
    expect(await screen.findByRole("cell", { name: "Mengubah pengaturan" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Muat catatan sebelumnya" })).not.toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText("Aksi"), "koreksi");
    await user.selectOptions(await screen.findByLabelText("Pelaku"), DAFTAR_STAF[2]?.id_pengguna ?? "");
    await user.type(screen.getByLabelText("Dari tanggal"), "2026-10-01");
    await user.click(screen.getByRole("button", { name: "Terapkan" }));
    await waitFor(() => expect(diminta.at(-1)?.get("aksi")).toBe("koreksi"));
    expect(diminta.at(-1)?.get("id_aktor")).toBe(DAFTAR_STAF[2]?.id_pengguna);
    expect(diminta.at(-1)?.get("dari")).toBe("2026-10-01");

    await user.click(screen.getByRole("button", { name: "Reset" }));
    await waitFor(() => expect(diminta.at(-1)?.get("aksi")).toBeNull());
  });

  it("menolak rentang terbalik dan menampilkan hasil kosong", async () => {
    const { user } = renderRute("/log-audit");
    expect(await screen.findByText(/Tidak ada catatan untuk filter ini/)).toBeInTheDocument();
    await user.type(screen.getByLabelText("Dari tanggal"), "2026-10-20");
    await user.type(screen.getByLabelText("Sampai tanggal"), "2026-10-01");
    await user.click(screen.getByRole("button", { name: "Terapkan" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Tanggal awal tidak boleh melewati tanggal akhir.");
  });

  it("gagal memuat log", async () => {
    server.use(http.get(`${API}/admin/log-audit`, () => problem(500, { title: "Log gagal dimuat" })));
    renderRute("/log-audit");
    expect(await screen.findByRole("alert")).toHaveTextContent("Log gagal dimuat");
  });
});
