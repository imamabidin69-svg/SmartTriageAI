import { act, screen, waitFor } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { BalasanEir } from "@/api/tipe";
import { bacaSesi, type SesiEirTersimpan, simpanSesi } from "@/lib/sesiEir";
import { renderRute } from "@/uji/render";
import { API, problem, server } from "@/uji/server";

const ID_SESI = "e0000000-0000-4000-8000-000000000001";
const PEMBUKA = "Halo, saya Eir. Keluhan apa yang paling mengganggu saat ini?";

function sesiTersimpan(ubah: Partial<SesiEirTersimpan> = {}): SesiEirTersimpan {
  return {
    idSesi: ID_SESI,
    tokenSesi: "token-sesi",
    kedaluwarsa: new Date(Date.now() + 3_600_000).toISOString(),
    pesan: [{ peran: "eir", teks: PEMBUKA }],
    status: "berjalan",
    bolehSelesai: false,
    jumlahJawaban: 0,
    ...ubah,
  };
}

function balasan(ubah: Partial<BalasanEir> = {}): BalasanEir {
  return { status: "berjalan", pesan: "Sejak kapan keluhannya?", jumlah_jawaban: 1, boleh_selesai: false, ...ubah };
}

function bukaPercakapan(ubah: Partial<SesiEirTersimpan> = {}) {
  simpanSesi(sesiTersimpan(ubah));
  return renderRute("/eir");
}

async function jawab(user: ReturnType<typeof renderRute>["user"], teks: string) {
  await user.type(screen.getByLabelText("Jawaban Anda"), teks);
  await user.click(screen.getByRole("button", { name: "Kirim jawaban" }));
}

afterEach(() => {
  window.location.hash = "";
});

describe("Persetujuan Eir", () => {
  it("tanpa tautan meminta kode QR dari perawat", async () => {
    renderRute("/eir");
    expect(await screen.findByText("Tautan Eir tidak lengkap")).toBeInTheDocument();
  });

  it("membaca token dari kode QR, menghapusnya dari alamat, lalu membuka sesi", async () => {
    window.history.replaceState(null, "", "/eir#t=token-qr");
    let dikirim: unknown;
    let header: string | null = "";
    server.use(
      http.post(`${API}/eir/sesi`, async ({ request }) => {
        dikirim = await request.json();
        return HttpResponse.json(
          { id_sesi: ID_SESI, token_sesi: "token-sesi", kedaluwarsa: "2099-01-01T00:00:00Z", pesan: PEMBUKA },
          { status: 201 },
        );
      }),
      http.post(`${API}/eir/sesi/:id/pesan`, ({ request }) => {
        header = request.headers.get("X-Token-Eir");
        return HttpResponse.json(balasan());
      }),
    );
    const { user } = renderRute("/eir");
    expect(await screen.findByRole("heading", { name: "Halo, saya Eir" })).toBeInTheDocument();
    expect(window.location.hash).toBe("");

    await user.click(screen.getByRole("button", { name: "Mulai percakapan" }));
    expect(screen.getByText("Pilih siapa yang mengisi.")).toBeInTheDocument();
    expect(screen.getByText("Centang persetujuan untuk memulai percakapan.")).toBeInTheDocument();

    await user.click(screen.getByLabelText("Keluarga pendamping"));
    await user.click(screen.getByLabelText(/setuju percakapan ini dicatat/));
    await user.click(screen.getByRole("button", { name: "Mulai percakapan" }));
    expect(await screen.findByText(PEMBUKA)).toBeInTheDocument();
    expect(dikirim).toEqual({ token: "token-qr", setuju: true, pengisi: "keluarga" });

    await jawab(user, "pusing");
    expect(await screen.findByText("Sejak kapan keluhannya?")).toBeInTheDocument();
    expect(header).toBe("token-sesi");
  });

  it("tautan kedaluwarsa ditampilkan dengan pesan dari server", async () => {
    window.history.replaceState(null, "", "/eir#t=token-lama");
    server.use(
      http.post(`${API}/eir/sesi`, () =>
        problem(401, {
          title: "Tautan Eir kedaluwarsa",
          detail: "Kode QR sudah lebih dari dua jam. Minta kode QR baru ke perawat.",
        }),
      ),
    );
    const { user } = renderRute("/eir");
    await user.click(await screen.findByLabelText("Saya pasien"));
    await user.click(screen.getByLabelText(/setuju percakapan ini dicatat/));
    await user.click(screen.getByRole("button", { name: "Mulai percakapan" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Minta kode QR baru ke perawat");
  });

  it("kode QR baru membuang sesi lama", async () => {
    simpanSesi(sesiTersimpan());
    window.history.replaceState(null, "", "/eir#t=token-baru");
    renderRute("/eir");
    expect(await screen.findByRole("heading", { name: "Halo, saya Eir" })).toBeInTheDocument();
    expect(bacaSesi()).toBeUndefined();
  });
});

describe("Percakapan Eir", () => {
  it("melanjutkan sesi tersimpan setelah halaman dimuat ulang", async () => {
    bukaPercakapan({
      pesan: [
        { peran: "eir", teks: PEMBUKA },
        { peran: "pengisi", teks: "pusing sejak pagi" },
      ],
    });
    expect(await screen.findByText("pusing sejak pagi")).toBeInTheDocument();
  });

  it("jawaban kosong tidak dikirim", async () => {
    const { user } = bukaPercakapan();
    await user.click(await screen.findByRole("button", { name: "Kirim jawaban" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Tulis jawaban terlebih dahulu.");
  });

  it("tanda bahaya menghentikan percakapan dan menampilkan arahan (TC-14)", async () => {
    const arahan = "Keluhan ini perlu segera dilihat perawat. Silakan langsung temui perawat di meja triase sekarang.";
    server.use(
      http.post(`${API}/eir/sesi/:id/pesan`, () => HttpResponse.json(balasan({ status: "dihentikan", pesan: arahan }))),
    );
    const { user } = bukaPercakapan();
    await jawab(await Promise.resolve(user), "dada saya seperti ditekan");
    const kartu = await screen.findByRole("alert");
    expect(kartu).toHaveTextContent("Perlu dilihat perawat sekarang");
    expect(kartu).toHaveTextContent(arahan);
    expect(screen.getByLabelText("Jawaban Anda")).toBeDisabled();
    expect(screen.getByPlaceholderText("Percakapan dihentikan")).toBeInTheDocument();
    expect(bacaSesi()?.status).toBe("dihentikan");
  });

  it("Groq tidak menjawab: jawaban tetap tersimpan dan diarahkan ke perawat (E3)", async () => {
    server.use(
      http.post(`${API}/eir/sesi/:id/pesan`, () =>
        problem(503, {
          title: "Layanan sedang tidak tersedia",
          detail: "Eir sedang tidak dapat menjawab. Silakan sampaikan keluhan langsung ke perawat.",
        }),
      ),
    );
    const { user } = bukaPercakapan();
    await jawab(user, "pusing");
    expect(await screen.findByRole("status", { name: "" })).toBeDefined();
    expect(await screen.findByText(/sampaikan keluhan langsung ke perawat/)).toBeInTheDocument();
    expect(screen.getByText("pusing")).toBeInTheDocument();
    expect(screen.getByLabelText("Jawaban Anda")).toHaveValue("");
    expect(bacaSesi()?.jumlahJawaban).toBe(1);
  });

  it("pesan terlalu cepat dikembalikan ke kotak jawaban", async () => {
    server.use(
      http.post(`${API}/eir/sesi/:id/pesan`, () =>
        problem(
          429,
          { detail: "Pesan dikirim terlalu cepat. Tunggu sebentar lalu kirim lagi." },
          { "Retry-After": "20" },
        ),
      ),
    );
    const { user } = bukaPercakapan();
    await jawab(user, "pusing");
    expect(await screen.findByRole("alert")).toHaveTextContent("terlalu cepat");
    expect(screen.getByLabelText("Jawaban Anda")).toHaveValue("pusing");
    expect(screen.queryByText("pusing", { selector: "p" })).not.toBeInTheDocument();
  });

  it("pesan field dari validasi server", async () => {
    server.use(
      http.post(`${API}/eir/sesi/:id/pesan`, () =>
        problem(422, {
          title: "Data tidak valid",
          errors: [{ field: "teks", pesan: "Pesan maksimal 1000 karakter." }],
        }),
      ),
    );
    const { user } = bukaPercakapan();
    await jawab(user, "pusing");
    expect(await screen.findByRole("alert")).toHaveTextContent("Pesan maksimal 1000 karakter.");
  });

  it.each([
    [{ status_sesi: "selesai" }, "Sesi Eir sudah berakhir.", "Percakapan selesai"],
    [{}, "Pasien sudah dipanggil untuk diperiksa. Sampaikan keluhan langsung ke petugas.", "Percakapan ditutup"],
  ])("konflik 409 mengunci kotak jawaban (%o)", async (ekstra, detail, placeholder) => {
    server.use(http.post(`${API}/eir/sesi/:id/pesan`, () => problem(409, { detail, ...ekstra })));
    const { user } = bukaPercakapan();
    await jawab(user, "pusing");
    expect(await screen.findByText(detail)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(placeholder)).toBeDisabled();
  });

  it("token sesi kedaluwarsa menutup percakapan", async () => {
    server.use(http.post(`${API}/eir/sesi/:id/pesan`, () => problem(401, { detail: "Sesi Eir sudah berakhir." })));
    const { user } = bukaPercakapan();
    await jawab(user, "pusing");
    expect(await screen.findByPlaceholderText("Percakapan ditutup")).toBeDisabled();
  });

  it("gangguan jaringan", async () => {
    server.use(http.post(`${API}/eir/sesi/:id/pesan`, () => HttpResponse.error()));
    const { user } = bukaPercakapan();
    await jawab(user, "pusing");
    expect(await screen.findByRole("alert")).toHaveTextContent("Server tidak dapat dihubungi");
  });

  it("menyelesaikan sesi setelah cukup jawaban (TC-15)", async () => {
    const penutup = "Terima kasih, jawaban sudah kami teruskan ke perawat.";
    server.use(
      http.post(`${API}/eir/sesi/:id/selesai`, () =>
        HttpResponse.json(balasan({ status: "selesai", pesan: penutup, jumlah_jawaban: 7 })),
      ),
    );
    const { user } = bukaPercakapan({ bolehSelesai: true, jumlahJawaban: 7 });
    await user.click(await screen.findByRole("button", { name: "Selesai dan kirim ke perawat" }));
    expect(await screen.findByText("Terima kasih")).toBeInTheDocument();
    expect(screen.getByText(penutup)).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Percakapan selesai")).toBeDisabled();
  });

  it("409 'Tekan Selesai' memunculkan tombol selesai", async () => {
    server.use(
      http.post(`${API}/eir/sesi/:id/pesan`, () =>
        problem(409, { detail: "Jawaban sudah cukup. Tekan Selesai untuk mengirim ringkasan ke perawat." }),
      ),
      http.post(`${API}/eir/sesi/:id/selesai`, () => problem(503, { detail: "Eir sedang tidak dapat menjawab." })),
    );
    const { user } = bukaPercakapan({ jumlahJawaban: 15 });
    await jawab(user, "tambahan");
    await user.click(await screen.findByRole("button", { name: "Selesai dan kirim ke perawat" }));
    expect(await screen.findByText("Eir sedang tidak dapat menjawab.")).toBeInTheDocument();
  });
});

describe("Jawaban suara Eir (W5)", () => {
  class PerekamPalsu {
    static isTypeSupported = (tipe: string) => tipe === "audio/webm;codecs=opus";
    state: "inactive" | "recording" = "inactive";
    mimeType: string;
    ondataavailable: ((event: { data: Blob }) => void) | null = null;
    onstop: (() => void) | null = null;
    constructor(_stream: unknown, opsi?: { mimeType?: string }) {
      this.mimeType = opsi?.mimeType ?? "";
    }
    start() {
      this.state = "recording";
    }
    stop() {
      this.state = "inactive";
      this.ondataavailable?.({ data: new Blob(["suara"], { type: "audio/webm" }) });
      this.onstop?.();
    }
  }

  function pasangMikrofon(getUserMedia = vi.fn().mockResolvedValue({ getTracks: () => [{ stop: vi.fn() }] })) {
    vi.stubGlobal("MediaRecorder", PerekamPalsu);
    Object.defineProperty(navigator, "mediaDevices", { value: { getUserMedia }, configurable: true });
    return getUserMedia;
  }

  it("merekam, mengirim, lalu menampilkan hasil ubah suara ke teks", async () => {
    pasangMikrofon();
    // FormData jsdom kehilangan nama berkas saat melewati fetch Node, jadi nama diperiksa saat ditambahkan.
    const tambah = vi.spyOn(FormData.prototype, "append");
    let adaBerkas = false;
    server.use(
      http.post(`${API}/eir/sesi/:id/suara`, async ({ request }) => {
        // Body dibaca mentah. request.formData() di Node 24 menolak File buatan jsdom saat mem-parse ulang.
        const isi = await request.text();
        adaBerkas =
          request.headers.get("Content-Type")?.startsWith("multipart/form-data") === true &&
          isi.includes('name="berkas"');
        return HttpResponse.json(balasan({ transkripsi: "pusing sejak pagi" }));
      }),
    );
    const { user } = bukaPercakapan();
    await user.click(await screen.findByRole("button", { name: "Jawab dengan suara" }));
    expect(screen.getByText(/Merekam/)).toBeInTheDocument();
    expect(screen.getByLabelText("Jawaban Anda")).toBeDisabled();
    await user.click(screen.getByRole("button", { name: "Berhenti merekam dan kirim" }));
    expect(await screen.findByText("pusing sejak pagi")).toBeInTheDocument();
    expect(screen.getByText("Sejak kapan keluhannya?")).toBeInTheDocument();
    expect(adaBerkas).toBe(true);
    const [nama, nilai] = tambah.mock.calls[0] ?? [];
    expect([nama, (nilai as File).name, (nilai as File).type]).toEqual([
      "berkas",
      "rekaman.webm",
      "audio/webm;codecs=opus",
    ]);
  });

  it("rekaman berhenti otomatis setelah 60 detik", async () => {
    pasangMikrofon();
    server.use(http.post(`${API}/eir/sesi/:id/suara`, () => HttpResponse.json(balasan({ transkripsi: null }))));
    const { user } = bukaPercakapan();
    vi.useFakeTimers({ shouldAdvanceTime: true });
    await user.click(await screen.findByRole("button", { name: "Jawab dengan suara" }));
    await act(async () => {
      vi.advanceTimersByTime(60_000);
    });
    vi.useRealTimers();
    expect(await screen.findByText("(rekaman suara)")).toBeInTheDocument();
  });

  it("mikrofon ditolak menampilkan saran mengetik", async () => {
    pasangMikrofon(vi.fn().mockRejectedValue(new Error("NotAllowedError")));
    const { user } = bukaPercakapan();
    await user.click(await screen.findByRole("button", { name: "Jawab dengan suara" }));
    expect(await screen.findByText(/Mikrofon tidak dapat dipakai/)).toBeInTheDocument();
  });

  it("rekaman yang tidak terdengar ditolak server", async () => {
    pasangMikrofon();
    server.use(
      http.post(`${API}/eir/sesi/:id/suara`, () =>
        problem(422, {
          title: "Data tidak valid",
          errors: [{ field: "berkas", pesan: "Suara tidak terdengar jelas." }],
        }),
      ),
    );
    const { user } = bukaPercakapan();
    await user.click(await screen.findByRole("button", { name: "Jawab dengan suara" }));
    await user.click(screen.getByRole("button", { name: "Berhenti merekam dan kirim" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Suara tidak terdengar jelas.");
  });

  it("tombol suara disembunyikan bila peramban tidak mendukung", async () => {
    bukaPercakapan();
    await screen.findByText(PEMBUKA);
    await waitFor(() => expect(screen.queryByRole("button", { name: "Jawab dengan suara" })).not.toBeInTheDocument());
  });
});
