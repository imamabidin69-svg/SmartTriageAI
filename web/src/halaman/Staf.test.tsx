import { screen, waitFor, within } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { describe, expect, it, vi } from "vitest";
import { renderRute } from "@/uji/render";
import { API, DAFTAR_STAF, problem, server } from "@/uji/server";

const SARI = DAFTAR_STAF[1];
const BUDI = DAFTAR_STAF[2];

async function bukaStaf() {
  const hasil = renderRute("/staf");
  await screen.findByRole("table");
  return hasil;
}

function baris(nama: string) {
  return screen.getByRole("row", { name: new RegExp(nama) });
}

describe("Kelola Staf", () => {
  it("menampilkan daftar staf dan menandai akun sendiri", async () => {
    await bukaStaf();
    expect(baris("Sari Perawat")).toHaveTextContent("Perawat");
    expect(baris("Budi Dokter")).toHaveTextContent("Nonaktif");
    const sendiri = baris("dr. Arif Hidayat");
    expect(sendiri).toHaveTextContent("(Anda)");
    expect(within(sendiri).queryByRole("button", { name: "Nonaktifkan" })).not.toBeInTheDocument();
  });

  it("menyaring berdasarkan peran dan status", async () => {
    const { user } = await bukaStaf();
    await user.selectOptions(screen.getByLabelText("Peran"), "dokter");
    expect(screen.queryByText("Sari Perawat")).not.toBeInTheDocument();
    expect(screen.getByText("Budi Dokter")).toBeInTheDocument();
    await user.selectOptions(screen.getByLabelText("Status"), "aktif");
    expect(screen.getByText(/Tidak ada staf yang cocok/)).toBeInTheDocument();
  });

  it("menambah staf lalu menampilkan password sementara sekali", async () => {
    let dikirim: unknown;
    server.use(
      http.post(`${API}/admin/staf`, async ({ request }) => {
        dikirim = await request.json();
        return HttpResponse.json(
          {
            staf: { ...SARI, id_pengguna: "d0000000-0000-4000-8000-000000000004", nama: "Rina", email: "rina@x.id" },
            password_sementara: "Kq7mPz2wXa9d",
          },
          { status: 201 },
        );
      }),
    );
    const { user } = await bukaStaf();
    // user-event memasang clipboard tiruan saat setup, jadi spy dipasang sesudahnya.
    const salin = vi.spyOn(navigator.clipboard, "writeText");
    await user.click(screen.getByRole("button", { name: "Tambah staf" }));
    const dialog = screen.getByRole("dialog", { name: "Tambah staf" });
    await user.type(within(dialog).getByLabelText("Nama"), "Rina");
    await user.type(within(dialog).getByLabelText("Email"), "rina@x.id");
    await user.selectOptions(within(dialog).getByLabelText("Peran"), "dokter");
    await user.click(within(dialog).getByRole("button", { name: "Tambah staf" }));

    const password = await screen.findByRole("dialog", { name: "Password sementara" });
    expect(password).toHaveTextContent("Kq7mPz2wXa9d");
    expect(dikirim).toEqual({ nama: "Rina", email: "rina@x.id", peran: "dokter" });
    await user.click(within(password).getByRole("button", { name: /Salin/ }));
    expect(salin).toHaveBeenCalledWith("Kq7mPz2wXa9d");
    expect(within(password).getByRole("button", { name: /Tersalin/ })).toBeInTheDocument();
    await user.click(within(password).getByRole("button", { name: "Sudah saya catat" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("validasi di klien dan pesan field dari server", async () => {
    server.use(
      http.post(`${API}/admin/staf`, () =>
        problem(409, {
          title: "Terjadi konflik data",
          errors: [{ field: "email", pesan: "Email sudah dipakai staf lain." }],
        }),
      ),
    );
    const { user } = await bukaStaf();
    await user.click(screen.getByRole("button", { name: "Tambah staf" }));
    const dialog = screen.getByRole("dialog", { name: "Tambah staf" });
    await user.click(within(dialog).getByRole("button", { name: "Tambah staf" }));
    expect(within(dialog).getByText("Nama wajib diisi.")).toBeInTheDocument();
    await user.type(within(dialog).getByLabelText("Nama"), "Rina");
    await user.type(within(dialog).getByLabelText("Email"), "sari@smarttriage.demo");
    await user.click(within(dialog).getByRole("button", { name: "Tambah staf" }));
    expect(await within(dialog).findByText("Email sudah dipakai staf lain.")).toBeInTheDocument();
    await user.click(within(dialog).getByRole("button", { name: "Batal" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("galat server tanpa field ditampilkan di atas form", async () => {
    server.use(http.post(`${API}/admin/staf`, () => problem(500, { title: "Terjadi kesalahan pada server" })));
    const { user } = await bukaStaf();
    await user.click(screen.getByRole("button", { name: "Tambah staf" }));
    const dialog = screen.getByRole("dialog", { name: "Tambah staf" });
    await user.type(within(dialog).getByLabelText("Nama"), "Rina");
    await user.type(within(dialog).getByLabelText("Email"), "rina@x.id");
    await user.click(within(dialog).getByRole("button", { name: "Tambah staf" }));
    expect(await within(dialog).findByRole("alert")).toHaveTextContent("Terjadi kesalahan pada server");
  });

  it("mengubah data hanya mengirim field yang berubah", async () => {
    let dikirim: unknown;
    server.use(
      http.patch(`${API}/admin/staf/:id`, async ({ request }) => {
        dikirim = await request.json();
        return HttpResponse.json({ staf: SARI, password_sementara: null });
      }),
    );
    const { user } = await bukaStaf();
    await user.click(within(baris("Sari Perawat")).getByRole("button", { name: "Ubah" }));
    const dialog = screen.getByRole("dialog", { name: "Ubah data staf" });
    const nama = within(dialog).getByLabelText("Nama");
    await user.clear(nama);
    await user.type(nama, "Sari Wulandari");
    await user.click(within(dialog).getByRole("button", { name: "Simpan perubahan" }));
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(dikirim).toEqual({ nama: "Sari Wulandari" });
    expect(await screen.findByText("Data Sari Perawat diperbarui.")).toBeInTheDocument();
  });

  it("menyimpan tanpa perubahan cukup menutup dialog", async () => {
    const patch = vi.fn();
    server.use(http.patch(`${API}/admin/staf/:id`, patch));
    const { user } = await bukaStaf();
    await user.click(within(baris("Budi Dokter")).getByRole("button", { name: "Ubah" }));
    const dialog = screen.getByRole("dialog", { name: "Ubah data staf" });
    await user.click(within(dialog).getByRole("button", { name: "Simpan perubahan" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(patch).not.toHaveBeenCalled();
  });

  it("menonaktifkan dan mengaktifkan akun lewat konfirmasi bernama", async () => {
    const dikirim: unknown[] = [];
    server.use(
      http.patch(`${API}/admin/staf/:id`, async ({ request }) => {
        dikirim.push(await request.json());
        return HttpResponse.json({ staf: SARI, password_sementara: null });
      }),
    );
    const { user } = await bukaStaf();
    await user.click(within(baris("Sari Perawat")).getByRole("button", { name: "Nonaktifkan" }));
    await user.click(screen.getByRole("button", { name: "Nonaktifkan Sari Perawat" }));
    expect(await screen.findByText("Akun Sari Perawat dinonaktifkan.")).toBeInTheDocument();
    await user.click(within(baris("Budi Dokter")).getByRole("button", { name: "Aktifkan" }));
    await user.click(screen.getByRole("button", { name: "Aktifkan Budi Dokter" }));
    expect(await screen.findByText("Akun Budi Dokter diaktifkan kembali.")).toBeInTheDocument();
    expect(dikirim).toEqual([{ is_active: false }, { is_active: true }]);
  });

  it("menampilkan penolakan server saat menonaktifkan", async () => {
    server.use(
      http.patch(`${API}/admin/staf/:id`, () =>
        problem(409, { detail: "Sistem harus punya minimal satu admin aktif." }),
      ),
    );
    const { user } = await bukaStaf();
    await user.click(within(baris("Sari Perawat")).getByRole("button", { name: "Nonaktifkan" }));
    await user.click(screen.getByRole("button", { name: "Nonaktifkan Sari Perawat" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("minimal satu admin aktif");
  });

  it("mengatur ulang password lalu menampilkan password sementara", async () => {
    server.use(
      http.patch(`${API}/admin/staf/:id`, () => HttpResponse.json({ staf: BUDI, password_sementara: "Zr8nTq4vLm2x" })),
    );
    const { user } = await bukaStaf();
    await user.click(within(baris("Budi Dokter")).getByRole("button", { name: "Atur ulang password" }));
    await user.click(screen.getByRole("button", { name: "Atur ulang password Budi Dokter" }));
    expect(await screen.findByRole("dialog", { name: "Password sementara" })).toHaveTextContent("Zr8nTq4vLm2x");
  });

  it("dialog atur ulang bisa dibatalkan dengan Escape", async () => {
    const { user } = await bukaStaf();
    await user.click(within(baris("Budi Dokter")).getByRole("button", { name: "Atur ulang password" }));
    const dialog = screen.getByRole("dialog", { name: "Atur ulang password" });
    dialog.dispatchEvent(new Event("cancel", { cancelable: true }));
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
  });

  it("gagal memuat daftar staf", async () => {
    server.use(http.get(`${API}/admin/staf`, () => problem(500, { title: "Terjadi kesalahan pada server" })));
    renderRute("/staf");
    expect(await screen.findByRole("alert")).toHaveTextContent("Terjadi kesalahan pada server");
  });
});
