import { Copy, Plus } from "@phosphor-icons/react";
import { type FormEvent, useMemo, useState } from "react";
import { z } from "zod";
import { useSaya, useStaf, useTambahStaf, useUbahStaf } from "@/api/admin";
import { ProblemError, pesanError } from "@/api/klien";
import type { Peran, Staf, StafPatch } from "@/api/tipe";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { Isian, Pilihan } from "@/components/ui/isian";
import { Memuat } from "@/components/ui/memuat";
import { tanggal } from "@/lib/format";
import { LABEL_PERAN } from "@/lib/label";
import { useNotifikasi } from "@/lib/notifikasi";
import { galatZod } from "@/lib/validasi";

const DAFTAR_PERAN: Peran[] = ["perawat", "dokter", "admin"];

// Aturan sama dengan StafRequest di backend; server tetap menjadi acuan akhir.
const skemaStaf = z.object({
  nama: z.string().trim().min(1, "Nama wajib diisi.").max(120, "Nama maksimal 120 karakter."),
  email: z
    .string()
    .trim()
    .min(1, "Email wajib diisi.")
    .max(150, "Email maksimal 150 karakter.")
    .email("Format email tidak valid."),
  peran: z.enum(["perawat", "dokter", "admin"], { message: "Pilih peran staf." }),
});

type IsianStaf = z.input<typeof skemaStaf>;

type Aksi =
  | { jenis: "tambah" }
  | { jenis: "ubah"; staf: Staf }
  | { jenis: "status"; staf: Staf }
  | { jenis: "atur-ulang"; staf: Staf }
  | { jenis: "password"; staf: Staf; password: string };

interface FormStafProps {
  awal: IsianStaf;
  label: string;
  menyimpan: boolean;
  galatServer?: ProblemError;
  onSimpan: (isi: z.output<typeof skemaStaf>) => void;
  onBatal: () => void;
}

function FormStaf({ awal, label, menyimpan, galatServer, onSimpan, onBatal }: FormStafProps) {
  const [isian, setIsian] = useState<IsianStaf>(awal);
  const [galatField, setGalatField] = useState<Record<string, string>>({});
  const galat = { ...galatServer?.pesanField, ...galatField };

  function kirim(event: FormEvent) {
    event.preventDefault();
    const hasil = skemaStaf.safeParse(isian);
    if (!hasil.success) {
      setGalatField(galatZod(hasil.error));
      return;
    }
    setGalatField({});
    onSimpan(hasil.data);
  }

  return (
    <form onSubmit={kirim} noValidate className="space-y-4">
      {galatServer && !galatServer.errors.length ? <Alert jenis="galat">{pesanError(galatServer)}</Alert> : null}
      <Isian
        label="Nama"
        value={isian.nama}
        onChange={(e) => setIsian({ ...isian, nama: e.target.value })}
        galat={galat.nama}
      />
      <Isian
        label="Email"
        type="email"
        value={isian.email}
        onChange={(e) => setIsian({ ...isian, email: e.target.value })}
        galat={galat.email}
      />
      <Pilihan
        label="Peran"
        value={isian.peran}
        onChange={(e) => setIsian({ ...isian, peran: e.target.value as Peran })}
        galat={galat.peran}
      >
        {DAFTAR_PERAN.map((peran) => (
          <option key={peran} value={peran}>
            {LABEL_PERAN[peran]}
          </option>
        ))}
      </Pilihan>
      <div className="flex justify-end gap-2 pt-2">
        <Button variant="outline" onClick={onBatal}>
          Batal
        </Button>
        <Button type="submit" disabled={menyimpan}>
          {menyimpan ? "Menyimpan..." : label}
        </Button>
      </div>
    </form>
  );
}

function PasswordSementara({ staf, password, onTutup }: { staf: Staf; password: string; onTutup: () => void }) {
  const [tersalin, setTersalin] = useState(false);
  async function salin() {
    await navigator.clipboard.writeText(password);
    setTersalin(true);
  }
  return (
    <div className="space-y-4">
      <p className="text-sm text-teks">
        Berikan password sementara ini kepada <strong>{staf.nama}</strong>. Staf diminta menggantinya setelah masuk.
      </p>
      <div className="flex items-center gap-2 rounded-md border border-garis bg-latar px-3 py-2">
        <code className="flex-1 font-mono text-base tracking-wide text-teks">{password}</code>
        <Button variant="outline" size="sm" onClick={salin}>
          <Copy size={16} aria-hidden /> {tersalin ? "Tersalin" : "Salin"}
        </Button>
      </div>
      <Alert jenis="peringatan">Password ini hanya ditampilkan sekali dan tidak bisa dilihat lagi.</Alert>
      <div className="flex justify-end">
        <Button onClick={onTutup}>Sudah saya catat</Button>
      </div>
    </div>
  );
}

function perubahan(staf: Staf, isi: z.output<typeof skemaStaf>): StafPatch {
  const patch: StafPatch = {};
  if (isi.nama !== staf.nama) patch.nama = isi.nama;
  if (isi.email.toLowerCase() !== staf.email) patch.email = isi.email;
  if (isi.peran !== staf.peran) patch.peran = isi.peran;
  return patch;
}

export function HalamanStaf() {
  const daftar = useStaf();
  const saya = useSaya();
  const tambah = useTambahStaf();
  const ubah = useUbahStaf();
  const tampilkan = useNotifikasi((s) => s.tampilkan);
  const [aksi, setAksi] = useState<Aksi | null>(null);
  const [filterPeran, setFilterPeran] = useState<"" | Peran>("");
  const [filterStatus, setFilterStatus] = useState<"" | "aktif" | "nonaktif">("");

  const terlihat = useMemo(
    () =>
      (daftar.data?.items ?? []).filter(
        (s) =>
          (!filterPeran || s.peran === filterPeran) && (!filterStatus || s.is_active === (filterStatus === "aktif")),
      ),
    [daftar.data, filterPeran, filterStatus],
  );

  function tutup() {
    setAksi(null);
    tambah.reset();
    ubah.reset();
  }

  function simpanBaru(isi: z.output<typeof skemaStaf>) {
    tambah.mutate(isi, {
      onSuccess: (hasil) => {
        tampilkan(`Akun ${hasil.staf.nama} dibuat.`);
        setAksi({ jenis: "password", staf: hasil.staf, password: hasil.password_sementara ?? "" });
      },
    });
  }

  function simpanUbah(staf: Staf, isi: z.output<typeof skemaStaf>) {
    const patch = perubahan(staf, isi);
    if (!Object.keys(patch).length) {
      tutup();
      return;
    }
    ubah.mutate(
      { id: staf.id_pengguna, isi: patch },
      {
        onSuccess: () => {
          tampilkan(`Data ${staf.nama} diperbarui.`);
          tutup();
        },
      },
    );
  }

  function ubahStatus(staf: Staf) {
    ubah.mutate(
      { id: staf.id_pengguna, isi: { is_active: !staf.is_active } },
      {
        onSuccess: () => {
          tampilkan(staf.is_active ? `Akun ${staf.nama} dinonaktifkan.` : `Akun ${staf.nama} diaktifkan kembali.`);
          tutup();
        },
      },
    );
  }

  function aturUlang(staf: Staf) {
    ubah.mutate(
      { id: staf.id_pengguna, isi: { atur_ulang_password: true } },
      { onSuccess: (hasil) => setAksi({ jenis: "password", staf, password: hasil.password_sementara ?? "" }) },
    );
  }

  const galatUbah = ubah.error instanceof ProblemError ? ubah.error : undefined;

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-[26px] font-bold text-teks">Kelola Staf</h1>
          <p className="mt-1 text-[15px] text-teks-2">
            Tambah, ubah, dan nonaktifkan akun staf, serta atur ulang password.
          </p>
        </div>
        <Button onClick={() => setAksi({ jenis: "tambah" })}>
          <Plus size={18} aria-hidden /> Tambah staf
        </Button>
      </div>

      {/* Filter dan tabel dalam satu kotak, seperti daftar di aplikasi rumah sakit. */}
      <Card className="overflow-x-auto p-0">
        <div className="flex flex-wrap items-end gap-4 border-b border-garis px-4 py-3.5">
          <div className="grid w-full gap-4 sm:w-auto sm:grid-cols-[13rem_13rem]">
            <Pilihan label="Peran" value={filterPeran} onChange={(e) => setFilterPeran(e.target.value as "" | Peran)}>
              <option value="">Semua peran</option>
              {DAFTAR_PERAN.map((peran) => (
                <option key={peran} value={peran}>
                  {LABEL_PERAN[peran]}
                </option>
              ))}
            </Pilihan>
            <Pilihan
              label="Status"
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value as "" | "aktif" | "nonaktif")}
            >
              <option value="">Semua status</option>
              <option value="aktif">Aktif</option>
              <option value="nonaktif">Nonaktif</option>
            </Pilihan>
          </div>
          {daftar.data ? <p className="ml-auto self-center text-sm text-teks-3">{terlihat.length} staf</p> : null}
        </div>
        {daftar.isPending ? <Memuat /> : null}
        {daftar.isError ? (
          <div className="p-5">
            <Alert jenis="galat">{pesanError(daftar.error)}</Alert>
          </div>
        ) : null}
        {daftar.data ? (
          terlihat.length ? (
            <table className="w-full min-w-[720px] text-left text-[15px]">
              <thead className="border-b border-garis bg-[#f7f8fa] text-sm text-teks-2">
                <tr>
                  <th scope="col" className="px-4 py-3 font-bold">
                    Nama
                  </th>
                  <th scope="col" className="px-4 py-3 font-bold">
                    Email
                  </th>
                  <th scope="col" className="px-4 py-3 font-bold">
                    Peran
                  </th>
                  <th scope="col" className="px-4 py-3 font-bold">
                    Status
                  </th>
                  <th scope="col" className="px-4 py-3 font-bold">
                    Dibuat
                  </th>
                  <th scope="col" className="px-4 py-3 text-right font-bold">
                    Aksi
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-garis-2">
                {terlihat.map((staf) => {
                  const diriSendiri = staf.id_pengguna === saya.data?.id_pengguna;
                  return (
                    <tr key={staf.id_pengguna}>
                      <td className="px-4 py-3 font-bold text-teks">
                        {staf.nama}
                        {diriSendiri ? <span className="ml-2 text-xs text-teks-3">(Anda)</span> : null}
                      </td>
                      <td className="px-4 py-3 text-teks">{staf.email}</td>
                      <td className="px-4 py-3 text-teks">{LABEL_PERAN[staf.peran]}</td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex items-center gap-2 ${staf.is_active ? "text-teks" : "text-teks-3"}`}
                        >
                          <span
                            aria-hidden
                            className={`size-2 rounded-full ${
                              staf.is_active ? "bg-rendah" : "border-[1.5px] border-belum bg-transparent"
                            }`}
                          />
                          {staf.is_active ? "Aktif" : "Nonaktif"}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-teks">{tanggal(staf.created_at)}</td>
                      <td className="px-4 py-3">
                        <div className="flex justify-end gap-0.5">
                          <Button variant="ghost" size="sm" onClick={() => setAksi({ jenis: "ubah", staf })}>
                            Ubah
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => setAksi({ jenis: "atur-ulang", staf })}>
                            Atur ulang password
                          </Button>
                          {diriSendiri ? null : (
                            <Button variant="ghost" size="sm" onClick={() => setAksi({ jenis: "status", staf })}>
                              {staf.is_active ? "Nonaktifkan" : "Aktifkan"}
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          ) : (
            <p className="p-8 text-center text-sm text-teks-2">
              Tidak ada staf yang cocok dengan filter. Ubah filter peran atau status.
            </p>
          )
        ) : null}
      </Card>

      <Dialog terbuka={aksi?.jenis === "tambah"} judul="Tambah staf" onTutup={tutup}>
        <FormStaf
          awal={{ nama: "", email: "", peran: "perawat" }}
          label="Tambah staf"
          menyimpan={tambah.isPending}
          galatServer={tambah.error instanceof ProblemError ? tambah.error : undefined}
          onSimpan={simpanBaru}
          onBatal={tutup}
        />
      </Dialog>

      <Dialog terbuka={aksi?.jenis === "ubah"} judul="Ubah data staf" onTutup={tutup}>
        {aksi?.jenis === "ubah" ? (
          <FormStaf
            awal={{ nama: aksi.staf.nama, email: aksi.staf.email, peran: aksi.staf.peran }}
            label="Simpan perubahan"
            menyimpan={ubah.isPending}
            galatServer={galatUbah}
            onSimpan={(isi) => simpanUbah(aksi.staf, isi)}
            onBatal={tutup}
          />
        ) : null}
      </Dialog>

      <Dialog
        terbuka={aksi?.jenis === "status"}
        judul={aksi?.jenis === "status" && aksi.staf.is_active ? "Nonaktifkan akun" : "Aktifkan akun"}
        onTutup={tutup}
      >
        {aksi?.jenis === "status" ? (
          <div className="space-y-4">
            <p className="text-sm text-teks">
              {aksi.staf.is_active
                ? `${aksi.staf.nama} langsung tidak bisa masuk setelah akun dinonaktifkan. Data triase yang pernah dibuatnya tetap tersimpan.`
                : `${aksi.staf.nama} bisa masuk lagi dengan password yang terakhir dipakai.`}
            </p>
            {galatUbah ? <Alert jenis="galat">{pesanError(galatUbah)}</Alert> : null}
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={tutup}>
                Batal
              </Button>
              <Button
                variant={aksi.staf.is_active ? "destructive" : "default"}
                disabled={ubah.isPending}
                onClick={() => ubahStatus(aksi.staf)}
              >
                {aksi.staf.is_active ? `Nonaktifkan ${aksi.staf.nama}` : `Aktifkan ${aksi.staf.nama}`}
              </Button>
            </div>
          </div>
        ) : null}
      </Dialog>

      <Dialog terbuka={aksi?.jenis === "atur-ulang"} judul="Atur ulang password" onTutup={tutup}>
        {aksi?.jenis === "atur-ulang" ? (
          <div className="space-y-4">
            <p className="text-sm text-teks">
              Password lama {aksi.staf.nama} tidak bisa dipakai lagi. Server membuat password sementara baru yang hanya
              ditampilkan sekali.
            </p>
            {galatUbah ? <Alert jenis="galat">{pesanError(galatUbah)}</Alert> : null}
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={tutup}>
                Batal
              </Button>
              <Button disabled={ubah.isPending} onClick={() => aturUlang(aksi.staf)}>
                Atur ulang password {aksi.staf.nama}
              </Button>
            </div>
          </div>
        ) : null}
      </Dialog>

      <Dialog terbuka={aksi?.jenis === "password"} judul="Password sementara" onTutup={tutup}>
        {aksi?.jenis === "password" ? (
          <PasswordSementara staf={aksi.staf} password={aksi.password} onTutup={tutup} />
        ) : null}
      </Dialog>
    </div>
  );
}
