import { screen } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";
import { renderRute } from "@/uji/render";
import { API, problem, server } from "@/uji/server";

async function isi(user: ReturnType<typeof renderRute>["user"], lama: string, baru: string, ulang: string) {
  if (lama) await user.type(await screen.findByLabelText("Password lama"), lama);
  if (baru) await user.type(screen.getByLabelText("Password baru"), baru);
  if (ulang) await user.type(screen.getByLabelText("Ulangi password baru"), ulang);
  await user.click(screen.getByRole("button", { name: "Simpan password baru" }));
}

describe("Ganti password", () => {
  it("memeriksa isian di klien", async () => {
    const { user } = renderRute("/akun/password");
    await screen.findByLabelText("Password lama");
    await isi(user, "", "pendek", "beda");
    expect(screen.getByText("Password lama wajib diisi.")).toBeInTheDocument();
    expect(screen.getByText("Password baru minimal 8 karakter.")).toBeInTheDocument();
    expect(screen.getByText("Konfirmasi password tidak sama.")).toBeInTheDocument();
  });

  it("password baru harus berbeda dari yang lama", async () => {
    const { user } = renderRute("/akun/password");
    await isi(user, "sama12345", "sama12345", "sama12345");
    expect(screen.getByText("Password baru harus berbeda dari password lama.")).toBeInTheDocument();
  });

  it("berhasil mengganti password", async () => {
    let dikirim: unknown;
    server.use(
      http.patch(`${API}/auth/password`, async ({ request }) => {
        dikirim = await request.json();
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const { user } = renderRute("/akun/password");
    await isi(user, "lama12345", "baru12345", "baru12345");
    expect(await screen.findByText("Password berhasil diganti.")).toBeInTheDocument();
    expect(dikirim).toEqual({ password_lama: "lama12345", password_baru: "baru12345" });
    expect(screen.getByLabelText("Password lama")).toHaveValue("");
  });

  it("menampilkan penolakan server di kolomnya", async () => {
    server.use(
      http.patch(`${API}/auth/password`, () =>
        problem(422, {
          title: "Data tidak valid",
          detail: "Periksa kembali isian yang ditandai.",
          errors: [{ field: "password_lama", pesan: "Password lama tidak cocok." }],
        }),
      ),
    );
    const { user } = renderRute("/akun/password");
    await isi(user, "salah1234", "baru12345", "baru12345");
    expect(await screen.findByText("Password lama tidak cocok.")).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("Periksa kembali isian yang ditandai.");
  });
});
