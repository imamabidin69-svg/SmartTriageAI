"use client";

import { type FormEvent, Fragment, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  useCreateStaffMutation,
  useStaffQuery,
  useToggleStaffMutation,
  useUpdateStaffMutation,
} from "@/hooks/useStaffQueries";
import {
  type FacilityBoundRole,
  FacilityBoundRoleSchema,
  RegisterStaffPayloadSchema,
  UpdateStaffPayloadSchema,
} from "@/lib/schemas/triase.schema";

const ROLE_LABEL: Record<FacilityBoundRole, string> = {
  perawat: "Perawat",
  dokter_pj: "Dokter Penanggung Jawab (DPJ)",
  petugas_pendaftaran: "Petugas Pendaftaran",
  admin_faskes: "Admin Faskes",
};

/**
 * StaffManagementClient - "use client": satu-satunya jalur registrasi akun
 * di seluruh aplikasi ini (Modul 6 Bab G, keputusan desain FR-01 lanjutan).
 * TIDAK ada endpoint publik untuk mendaftar sendiri — hanya Admin Faskes
 * yang login yang bisa mengakses komponen ini (ditegakkan di server, lihat
 * app/(protected)/admin/staff/page.tsx dan Route Handler-nya).
 */
export function StaffManagementClient({ faskesNama, currentUserId }: { faskesNama: string; currentUserId: string }) {
  const { data: staff, isPending, isError, error } = useStaffQuery();
  const createMutation = useCreateStaffMutation();
  const toggleMutation = useToggleStaffMutation();
  const updateMutation = useUpdateStaffMutation();
  const [showForm, setShowForm] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [formKey, setFormKey] = useState(0); // dipakai untuk mereset form setelah submit berhasil
  const [searchTerm, setSearchTerm] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editFieldErrors, setEditFieldErrors] = useState<Record<string, string>>({});

  const filteredStaff = staff?.filter((u) => {
    const q = searchTerm.trim().toLowerCase();
    if (!q) return true;
    return u.nama.toLowerCase().includes(q) || u.email.toLowerCase().includes(q);
  });

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setFieldErrors({});
    const fd = new FormData(e.currentTarget);
    const raw = {
      nama: fd.get("nama")?.toString() ?? "",
      email: fd.get("email")?.toString() ?? "",
      password: fd.get("password")?.toString() ?? "",
      role: fd.get("role")?.toString(),
    };
    const parsed = RegisterStaffPayloadSchema.safeParse(raw);
    if (!parsed.success) {
      const errors: Record<string, string> = {};
      for (const issue of parsed.error.issues) errors[issue.path.join(".")] = issue.message;
      setFieldErrors(errors);
      return;
    }

    createMutation.mutate(parsed.data, {
      onSuccess: () => {
        setShowForm(false);
        setFormKey((k) => k + 1);
      },
      onError: (err) => {
        setFieldErrors({ email: err instanceof Error ? err.message : "Gagal mendaftarkan akun." });
      },
    });
  }

  function handleEditSubmit(e: FormEvent<HTMLFormElement>, id: string) {
    e.preventDefault();
    setEditFieldErrors({});
    const fd = new FormData(e.currentTarget);
    const raw = {
      nama: fd.get("nama")?.toString() ?? "",
      email: fd.get("email")?.toString() ?? "",
      role: fd.get("role")?.toString(),
    };
    const parsed = UpdateStaffPayloadSchema.safeParse(raw);
    if (!parsed.success) {
      const errors: Record<string, string> = {};
      for (const issue of parsed.error.issues) errors[issue.path.join(".")] = issue.message;
      setEditFieldErrors(errors);
      return;
    }

    updateMutation.mutate(
      { id, input: parsed.data },
      {
        onSuccess: () => setEditingId(null),
        onError: (err) => {
          setEditFieldErrors({ email: err instanceof Error ? err.message : "Gagal menyimpan perubahan." });
        },
      },
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-200">Kelola Akun Staf</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Faskes: <strong>{faskesNama}</strong> — registrasi akun hanya dapat dilakukan dari sini.
          </p>
        </div>
        <Button type="button" onClick={() => setShowForm((s) => !s)}>
          {showForm ? "Batal" : "+ Tambah Akun Staf"}
        </Button>
      </div>

      {showForm && (
        <form
          key={formKey}
          onSubmit={handleSubmit}
          className="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm space-y-4"
          noValidate
        >
          <div>
            <label
              htmlFor="faskesNamaDisplay"
              className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1"
            >
              Faskes
            </label>
            <input
              type="text"
              id="faskesNamaDisplay"
              value={faskesNama}
              disabled
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-sm bg-slate-100 dark:bg-slate-900 text-slate-500 dark:text-slate-400"
            />
            <p className="text-xs text-slate-400 mt-1">
              Akun baru otomatis terdaftar di faskes ini — tidak bisa diubah dari form ini.
            </p>
          </div>

          <div>
            <label htmlFor="nama" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Nama Lengkap <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="nama"
              name="nama"
              required
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm bg-white dark:bg-slate-900 dark:text-slate-200"
              placeholder="Contoh: Ns. Dewi Anggraini"
            />
            {fieldErrors.nama && (
              <p className="text-xs text-red-600 mt-1" role="alert">
                {fieldErrors.nama}
              </p>
            )}
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Email <span className="text-red-500">*</span>
            </label>
            <input
              type="email"
              id="email"
              name="email"
              required
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm bg-white dark:bg-slate-900 dark:text-slate-200"
              placeholder="nama@faskes.id"
            />
            {fieldErrors.email && (
              <p className="text-xs text-red-600 mt-1" role="alert">
                {fieldErrors.email}
              </p>
            )}
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Password Awal <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="password"
              name="password"
              required
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm bg-white dark:bg-slate-900 dark:text-slate-200 font-mono"
              placeholder="Minimal 8 karakter"
            />
            <p className="text-xs text-slate-400 mt-1">
              Sampaikan password ini kepada staf secara langsung. Sarankan mereka menggantinya setelah masuk pertama
              kali.
            </p>
            {fieldErrors.password && (
              <p className="text-xs text-red-600 mt-1" role="alert">
                {fieldErrors.password}
              </p>
            )}
          </div>

          <div>
            <label htmlFor="role" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Peran <span className="text-red-500">*</span>
            </label>
            <select
              id="role"
              name="role"
              defaultValue="perawat"
              className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-slate-900 dark:text-slate-200"
            >
              {FacilityBoundRoleSchema.options.map((r) => (
                <option key={r} value={r}>
                  {ROLE_LABEL[r]}
                </option>
              ))}
            </select>
            {fieldErrors.role && (
              <p className="text-xs text-red-600 mt-1" role="alert">
                {fieldErrors.role}
              </p>
            )}
          </div>

          <Button type="submit" disabled={createMutation.isPending}>
            {createMutation.isPending ? "Mendaftarkan…" : "Daftarkan Akun"}
          </Button>
        </form>
      )}

      {staff && staff.length > 0 && (
        <div className="relative max-w-sm">
          <input
            type="search"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Cari nama atau email staf…"
            aria-label="Cari akun staf"
            className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm bg-white dark:bg-slate-900 dark:text-slate-200"
          />
        </div>
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
          {error instanceof Error ? error.message : "Gagal memuat daftar staf."}
        </div>
      )}

      {staff && (
        <Card padding="none" className="overflow-hidden">
          {filteredStaff && filteredStaff.length === 0 ? (
            <p className="p-4 text-sm text-slate-500 dark:text-slate-400">
              Tidak ada staf yang cocok dengan pencarian &quot;{searchTerm}&quot;.
            </p>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-slate-50 dark:bg-slate-900 text-left">
                <tr>
                  <th className="px-4 py-3 font-semibold text-slate-700 dark:text-slate-300">Nama</th>
                  <th className="px-4 py-3 font-semibold text-slate-700 dark:text-slate-300">Email</th>
                  <th className="px-4 py-3 font-semibold text-slate-700 dark:text-slate-300">Peran</th>
                  <th className="px-4 py-3 font-semibold text-slate-700 dark:text-slate-300">Status</th>
                  <th className="px-4 py-3 font-semibold text-slate-700 dark:text-slate-300">Aksi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {filteredStaff?.map((u) => (
                  <Fragment key={u.id}>
                    <tr>
                      <td className="px-4 py-3 text-slate-900 dark:text-slate-200">{u.nama}</td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{u.email}</td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-400">
                        {ROLE_LABEL[u.role as FacilityBoundRole] ?? u.role}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={
                            u.isActive
                              ? "inline-block px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300"
                              : "inline-block px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-900 text-slate-500 dark:text-slate-400"
                          }
                        >
                          {u.isActive ? "Aktif" : "Nonaktif"}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {u.id === currentUserId ? (
                          <span className="text-xs text-slate-400">Akun Anda</span>
                        ) : (
                          <div className="flex flex-wrap gap-2">
                            <Button
                              type="button"
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                setEditFieldErrors({});
                                setEditingId((cur) => (cur === u.id ? null : u.id));
                              }}
                            >
                              {editingId === u.id ? "Tutup" : "Edit"}
                            </Button>
                            <Button
                              type="button"
                              variant={u.isActive ? "outline" : "secondary"}
                              size="sm"
                              disabled={toggleMutation.isPending}
                              onClick={() => toggleMutation.mutate({ id: u.id, isActive: !u.isActive })}
                            >
                              {u.isActive ? "Nonaktifkan" : "Aktifkan"}
                            </Button>
                          </div>
                        )}
                      </td>
                    </tr>
                    {editingId === u.id && (
                      <tr>
                        <td colSpan={5} className="px-4 py-4 bg-slate-50 dark:bg-slate-900/60">
                          <form
                            onSubmit={(e) => handleEditSubmit(e, u.id)}
                            className="grid grid-cols-1 sm:grid-cols-4 gap-3 items-end"
                            aria-label={`Form edit akun ${u.nama}`}
                          >
                            <div>
                              <label
                                htmlFor={`edit-nama-${u.id}`}
                                className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1"
                              >
                                Nama Lengkap
                              </label>
                              <input
                                type="text"
                                id={`edit-nama-${u.id}`}
                                name="nama"
                                defaultValue={u.nama}
                                required
                                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-sm bg-white dark:bg-slate-800 dark:text-slate-200"
                              />
                              {editFieldErrors.nama && (
                                <p className="text-xs text-red-600 mt-1" role="alert">
                                  {editFieldErrors.nama}
                                </p>
                              )}
                            </div>
                            <div>
                              <label
                                htmlFor={`edit-email-${u.id}`}
                                className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1"
                              >
                                Email
                              </label>
                              <input
                                type="email"
                                id={`edit-email-${u.id}`}
                                name="email"
                                defaultValue={u.email}
                                required
                                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-sm bg-white dark:bg-slate-800 dark:text-slate-200"
                              />
                              {editFieldErrors.email && (
                                <p className="text-xs text-red-600 mt-1" role="alert">
                                  {editFieldErrors.email}
                                </p>
                              )}
                            </div>
                            <div>
                              <label
                                htmlFor={`edit-role-${u.id}`}
                                className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1"
                              >
                                Peran
                              </label>
                              <select
                                id={`edit-role-${u.id}`}
                                name="role"
                                defaultValue={u.role}
                                className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-slate-800 dark:text-slate-200"
                              >
                                {FacilityBoundRoleSchema.options.map((r) => (
                                  <option key={r} value={r}>
                                    {ROLE_LABEL[r]}
                                  </option>
                                ))}
                              </select>
                            </div>
                            <div className="flex gap-2">
                              <Button type="submit" size="sm" disabled={updateMutation.isPending}>
                                {updateMutation.isPending ? "Menyimpan…" : "Simpan"}
                              </Button>
                              <Button type="button" variant="outline" size="sm" onClick={() => setEditingId(null)}>
                                Batal
                              </Button>
                            </div>
                          </form>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                ))}
              </tbody>
            </table>
          )}
        </Card>
      )}
    </div>
  );
}
