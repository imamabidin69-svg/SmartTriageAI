"use client";

import Link from "next/link";
import { type FormEvent, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { usePasienQuery, useRegisterPasienMutation } from "@/hooks/usePasienQueries";
import { RegisterPasienPayloadSchema } from "@/lib/schemas/pasien.schema";

function formatTanggal(iso?: string): string {
  if (!iso) return "-";
  try {
    return new Date(iso).toLocaleDateString("id-ID", { day: "2-digit", month: "short", year: "numeric" });
  } catch {
    return iso;
  }
}

export function PasienManagementClient({ showRiwayatLink }: { showRiwayatLink: boolean }) {
  const { data: pasienList, isPending, isError, error } = usePasienQuery();
  const registerMutation = useRegisterPasienMutation();
  const [showForm, setShowForm] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [searchTerm, setSearchTerm] = useState("");
  const [formKey, setFormKey] = useState(0);

  const filtered = pasienList?.filter((p) => {
    const q = searchTerm.trim().toLowerCase();
    if (!q) return true;
    return p.nama.toLowerCase().includes(q) || (p.nik ?? "").includes(q);
  });

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setFieldErrors({});
    const fd = new FormData(e.currentTarget);
    const raw = {
      nama: fd.get("nama")?.toString() ?? "",
      nik: fd.get("nik")?.toString() || undefined,
      tanggalLahir: fd.get("tanggalLahir")?.toString() || undefined,
      jenisKelamin: fd.get("jenisKelamin")?.toString() || undefined,
      alamat: fd.get("alamat")?.toString() || undefined,
      noTelepon: fd.get("noTelepon")?.toString() || undefined,
    };
    const parsed = RegisterPasienPayloadSchema.safeParse(raw);
    if (!parsed.success) {
      const errors: Record<string, string> = {};
      for (const issue of parsed.error.issues) errors[issue.path.join(".")] = issue.message;
      setFieldErrors(errors);
      return;
    }
    registerMutation.mutate(parsed.data, {
      onSuccess: () => {
        setShowForm(false);
        setFormKey((k) => k + 1);
      },
      onError: (err) => setFieldErrors({ nama: err instanceof Error ? err.message : "Gagal registrasi pasien." }),
    });
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-200">Registrasi Pasien</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Daftarkan identitas pasien sebelum menjalani pemeriksaan triase.
          </p>
        </div>
        <Button type="button" onClick={() => setShowForm((s) => !s)}>
          {showForm ? "Batal" : "+ Registrasi Pasien Baru"}
        </Button>
      </div>

      {showForm && (
        <form
          key={formKey}
          onSubmit={handleSubmit}
          className="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm space-y-4"
          noValidate
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label htmlFor="nama" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Nama Lengkap <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                id="nama"
                name="nama"
                required
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-sm bg-white dark:bg-slate-900 dark:text-slate-200"
              />
              {fieldErrors.nama && (
                <p className="text-xs text-red-600 mt-1" role="alert">
                  {fieldErrors.nama}
                </p>
              )}
            </div>
            <div>
              <label htmlFor="nik" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                NIK
              </label>
              <input
                type="text"
                id="nik"
                name="nik"
                maxLength={16}
                placeholder="16 digit (opsional)"
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-sm bg-white dark:bg-slate-900 dark:text-slate-200"
              />
              {fieldErrors.nik && (
                <p className="text-xs text-red-600 mt-1" role="alert">
                  {fieldErrors.nik}
                </p>
              )}
            </div>
            <div>
              <label
                htmlFor="tanggalLahir"
                className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1"
              >
                Tanggal Lahir
              </label>
              <input
                type="date"
                id="tanggalLahir"
                name="tanggalLahir"
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-sm bg-white dark:bg-slate-900 dark:text-slate-200"
              />
            </div>
            <div>
              <label
                htmlFor="jenisKelamin"
                className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1"
              >
                Jenis Kelamin
              </label>
              <select
                id="jenisKelamin"
                name="jenisKelamin"
                defaultValue=""
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-sm bg-white dark:bg-slate-900 dark:text-slate-200"
              >
                <option value="">-- Pilih --</option>
                <option value="laki_laki">Laki-laki</option>
                <option value="perempuan">Perempuan</option>
              </select>
            </div>
            <div>
              <label htmlFor="noTelepon" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                No. Telepon
              </label>
              <input
                type="text"
                id="noTelepon"
                name="noTelepon"
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-sm bg-white dark:bg-slate-900 dark:text-slate-200"
              />
            </div>
            <div className="sm:col-span-2">
              <label htmlFor="alamat" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Alamat
              </label>
              <input
                type="text"
                id="alamat"
                name="alamat"
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-sm bg-white dark:bg-slate-900 dark:text-slate-200"
              />
            </div>
          </div>
          <Button type="submit" disabled={registerMutation.isPending}>
            {registerMutation.isPending ? "Menyimpan…" : "Daftarkan Pasien"}
          </Button>
        </form>
      )}

      {pasienList && pasienList.length > 0 && (
        <input
          type="search"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Cari nama atau NIK pasien…"
          aria-label="Cari pasien"
          className="max-w-sm w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-sm bg-white dark:bg-slate-900 dark:text-slate-200"
        />
      )}

      {isPending && (
        <div className="animate-pulse space-y-2" aria-busy="true">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-14 bg-slate-100 dark:bg-slate-900 rounded-lg" />
          ))}
        </div>
      )}

      {isError && (
        <div
          className="rounded-lg border border-red-200 bg-red-50 dark:bg-red-950/30 p-4 text-red-800 dark:text-red-300"
          role="alert"
        >
          {error instanceof Error ? error.message : "Gagal memuat daftar pasien."}
        </div>
      )}

      {pasienList && (
        <Card padding="none" className="overflow-hidden">
          {filtered && filtered.length === 0 ? (
            <p className="p-4 text-sm text-slate-500 dark:text-slate-400">Belum ada pasien terdaftar.</p>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-slate-50 dark:bg-slate-900 text-left">
                <tr>
                  <th className="px-4 py-3 font-semibold text-slate-700 dark:text-slate-300">Nama</th>
                  <th className="px-4 py-3 font-semibold text-slate-700 dark:text-slate-300">NIK</th>
                  <th className="px-4 py-3 font-semibold text-slate-700 dark:text-slate-300">Tanggal Lahir</th>
                  <th className="px-4 py-3 font-semibold text-slate-700 dark:text-slate-300">Terdaftar</th>
                  {showRiwayatLink && (
                    <th className="px-4 py-3 font-semibold text-slate-700 dark:text-slate-300">Aksi</th>
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {filtered?.map((p) => (
                  <tr key={p.id}>
                    <td className="px-4 py-3 text-slate-900 dark:text-slate-200">{p.nama}</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{p.nik ?? "-"}</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{formatTanggal(p.tanggalLahir)}</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{formatTanggal(p.waktuDaftar)}</td>
                    {showRiwayatLink && (
                      <td className="px-4 py-3">
                        <Link
                          href={`/riwayat-pasien?nama=${encodeURIComponent(p.nama)}`}
                          className="text-sm font-medium text-blue-600 dark:text-blue-400 hover:underline"
                        >
                          Lihat Riwayat
                        </Link>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>
      )}
    </div>
  );
}
