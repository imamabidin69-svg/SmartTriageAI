import { screen, waitFor } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";
import { PESAN_BUKAN_ADMIN } from "@/layout/PenjagaAdmin";
import { renderRute } from "@/uji/render";
import { ADMIN, API, problem, server } from "@/uji/server";

function belumMasuk() {
  server.use(http.get(`${API}/auth/me`, () => problem(401, { title: "Belum masuk" })));
}

describe("Halaman login", () => {
  it("admin masuk lalu diarahkan ke Kelola Staf", async () => {
    belumMasuk();
    let isiLogin: unknown;
    server.use(
      http.post(`${API}/auth/login`, async ({ request }) => {
        isiLogin = await request.json();
        return HttpResponse.json({ pengguna: ADMIN });
      }),
    );
    const { user, router } = renderRute("/login");
    await user.type(await screen.findByLabelText("Email"), "admin@smarttriage.demo");
    await user.type(screen.getByLabelText("Password"), "rahasia123");
    await user.click(screen.getByRole("button", { name: "Masuk" }));
    await waitFor(() => expect(router.state.location.pathname).toBe("/staf"));
    expect(isiLogin).toEqual({ email: "admin@smarttriage.demo", password: "rahasia123" });
  });

  it("memeriksa isian sebelum dikirim", async () => {
    belumMasuk();
    const { user } = renderRute("/login");
    await user.type(await screen.findByLabelText("Email"), "bukan-email");
    await user.click(screen.getByRole("button", { name: "Masuk" }));
    expect(await screen.findByText("Format email tidak valid.")).toBeInTheDocument();
    expect(screen.getByText("Password wajib diisi.")).toBeInTheDocument();
  });

  it("menampilkan pesan dari server saat password salah", async () => {
    belumMasuk();
    server.use(
      http.post(`${API}/auth/login`, () =>
        problem(401, { title: "Email atau password salah", detail: "Email atau password salah." }),
      ),
    );
    const { user } = renderRute("/login");
    await user.type(await screen.findByLabelText("Email"), "admin@smarttriage.demo");
    await user.type(screen.getByLabelText("Password"), "salah");
    await user.click(screen.getByRole("button", { name: "Masuk" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Email atau password salah.");
  });

  it("perawat ditolak dengan arahan ke aplikasi Android dan sesinya dihapus (keputusan W4)", async () => {
    belumMasuk();
    let keluar = 0;
    server.use(
      http.post(`${API}/auth/login`, () => HttpResponse.json({ pengguna: { ...ADMIN, peran: "perawat" } })),
      http.post(`${API}/auth/logout`, () => {
        keluar += 1;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const { user, router } = renderRute("/login");
    await user.type(await screen.findByLabelText("Email"), "sari@smarttriage.demo");
    await user.type(screen.getByLabelText("Password"), "rahasia123");
    await user.click(screen.getByRole("button", { name: "Masuk" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(PESAN_BUKAN_ADMIN);
    expect(keluar).toBe(1);
    expect(router.state.location.pathname).toBe("/login");
  });

  it("admin yang sudah masuk langsung diarahkan", async () => {
    const { router } = renderRute("/login");
    await waitFor(() => expect(router.state.location.pathname).toBe("/staf"));
  });
});

describe("Penjaga halaman admin", () => {
  it("pengunjung yang belum masuk diarahkan ke login lalu kembali setelah masuk", async () => {
    belumMasuk();
    server.use(http.post(`${API}/auth/login`, () => HttpResponse.json({ pengguna: ADMIN })));
    const { user, router } = renderRute("/rekap");
    await waitFor(() => expect(router.state.location.pathname).toBe("/login"));
    await user.type(await screen.findByLabelText("Email"), "admin@smarttriage.demo");
    await user.type(screen.getByLabelText("Password"), "rahasia123");
    await user.click(screen.getByRole("button", { name: "Masuk" }));
    await waitFor(() => expect(router.state.location.pathname).toBe("/rekap"));
  });

  it("sesi dokter yang masih tersimpan diarahkan ke login dengan pesan", async () => {
    server.use(http.get(`${API}/auth/me`, () => HttpResponse.json({ ...ADMIN, peran: "dokter" })));
    renderRute("/staf");
    expect(await screen.findByRole("alert")).toHaveTextContent(PESAN_BUKAN_ADMIN);
  });

  it("server bermasalah saat memeriksa sesi", async () => {
    server.use(http.get(`${API}/auth/me`, () => problem(500, { title: "Terjadi kesalahan pada server" })));
    renderRute("/staf");
    expect(await screen.findByText("Sesi tidak dapat diperiksa")).toBeInTheDocument();
  });
});

describe("Layout admin", () => {
  it("menampilkan menu, nama admin, dan bisa keluar", async () => {
    let keluar = 0;
    server.use(
      http.post(`${API}/auth/logout`, () => {
        keluar += 1;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const { user, router } = renderRute("/staf");
    expect(await screen.findByText("dr. Arif Hidayat · Admin ICU")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Pengaturan" })).toHaveAttribute("href", "/pengaturan");
    await user.click(screen.getByRole("button", { name: "Keluar" }));
    await waitFor(() => expect(router.state.location.pathname).toBe("/login"));
    expect(keluar).toBe(1);
  });

  it("menu ponsel bisa dibuka dan ditutup", async () => {
    const { user, router } = renderRute("/staf");
    await user.click(await screen.findByRole("button", { name: "Buka menu" }));
    await user.click(screen.getAllByRole("link", { name: "Ganti password" })[0] as HTMLElement);
    await waitFor(() => expect(router.state.location.pathname).toBe("/akun/password"));
    expect(screen.queryByRole("button", { name: "Tutup menu" })).not.toBeInTheDocument();
  });

  it("keluar tetap berhasil walau sesi sudah habis", async () => {
    server.use(http.post(`${API}/auth/logout`, () => problem(401, { title: "Sesi berakhir" })));
    const { user, router } = renderRute("/staf");
    await user.click(await screen.findByRole("button", { name: "Buka menu" }));
    const tombol = screen.getAllByRole("button", { name: "Keluar" });
    await user.click(tombol[tombol.length - 1] as HTMLElement);
    await waitFor(() => expect(router.state.location.pathname).toBe("/login"));
  });

  it("alamat yang tidak ada menampilkan halaman tidak ditemukan", async () => {
    renderRute("/tidak-ada");
    expect(await screen.findByText("Halaman tidak ditemukan")).toBeInTheDocument();
  });
});
