"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";
import { ZodError } from "zod";
import { Button } from "@/components/ui/button";
import { usePasienQuery } from "@/hooks/usePasienQueries";
import { useSubmitTriaseMutation } from "@/hooks/useTriaseQueries";
import type { Pasien } from "@/lib/schemas/pasien.schema";
import { type TriageInput, TriageInputSchema } from "@/lib/schemas/triase.schema";
import { checkVitalWarnings } from "@/lib/vital-warnings";

function buildInputFromForm(form: HTMLFormElement, pasienTerpilih: Pasien | null): unknown {
  const fd = new FormData(form);
  const num = (name: string): number => Number(fd.get(name));
  return {
    idPasien: pasienTerpilih ? pasienTerpilih.id : crypto.randomUUID(),
    namaPasien: pasienTerpilih ? pasienTerpilih.nama : (fd.get("namaPasien")?.toString() ?? ""),
    gejala: fd.get("gejala")?.toString() ?? "",
    keluhanUtama: fd.get("keluhanUtama")?.toString() ?? "",
    riwayatSingkat: fd.get("riwayatSingkat")?.toString() || undefined,
    tandaVital: {
      tekananDarahSistolik: num("tekananDarahSistolik"),
      tekananDarahDiastolik: num("tekananDarahDiastolik"),
      suhuTubuh: num("suhuTubuh"),
      nadiPerMenit: num("nadiPerMenit"),
      lajuNapas: num("lajuNapas"),
      saturasiOksigen: num("saturasiOksigen"),
    },
  };
}

/**
 * TriaseFormClient - "use client": form interaktif (event handler, state
 * error per-field) dan memanggil useSubmitTriaseMutation (TanStack Query
 * useMutation, Modul 7 Bab C). Validasi Zod dijalankan DUA KALI by design:
 * di sini (fail-fast, UX responsif) dan lagi di Route Handler server
 * (pertahanan berlapis — klien tidak pernah dipercaya sepenuhnya).
 *
 * Tanda vital yang tidak lazim TIDAK ditolak otomatis — ditampilkan sebagai
 * dialog konfirmasi (pendingConfirm) yang meminta tenaga medis memastikan
 * data sudah benar sebelum lanjut, alih-alih memblokir input sama sekali
 * (kasus gawat darurat sungguhan bisa saja punya nilai ekstrem).
 */
export function TriaseFormClient() {
  const router = useRouter();
  const mutation = useSubmitTriaseMutation();
  const { data: pasienList } = usePasienQuery();
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [pendingConfirm, setPendingConfirm] = useState<{ input: TriageInput; warnings: string[] } | null>(null);
  const [pasienTerpilih, setPasienTerpilih] = useState<Pasien | null>(null);
  const [pasienSearch, setPasienSearch] = useState("");
  const [showPasienDropdown, setShowPasienDropdown] = useState(false);
  const [modePasienBaru, setModePasienBaru] = useState(false);

  const pasienCocok =
    pasienSearch.trim().length > 0
      ? pasienList?.filter((p) => p.nama.toLowerCase().includes(pasienSearch.trim().toLowerCase())).slice(0, 6)
      : pasienList?.slice(0, 6);

  function doSubmit(input: TriageInput) {
    mutation.mutate(input, {
      onSuccess: (record) => {
        router.push(`/triase/${record.idTriase}`);
      },
      onError: (err) => {
        if (err instanceof ZodError) {
          const errors: Record<string, string> = {};
          for (const issue of err.issues) errors[issue.path.join(".")] = issue.message;
          setFieldErrors(errors);
        }
      },
    });
  }

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setFieldErrors({});
    setPendingConfirm(null);

    if (!pasienTerpilih && !modePasienBaru) {
      setFieldErrors({ namaPasien: 'Pilih pasien terdaftar, atau klik "Pasien belum terdaftar" untuk input manual.' });
      return;
    }

    const raw = buildInputFromForm(e.currentTarget, pasienTerpilih);
    const parsed = TriageInputSchema.safeParse(raw);

    if (!parsed.success) {
      const errors: Record<string, string> = {};
      for (const issue of parsed.error.issues) {
        errors[issue.path.join(".")] = issue.message;
      }
      setFieldErrors(errors);
      return;
    }

    const warnings = checkVitalWarnings(parsed.data.tandaVital);
    if (warnings.length > 0) {
      // Jangan langsung kirim — tampilkan dialog konfirmasi dulu.
      setPendingConfirm({ input: parsed.data, warnings });
      return;
    }

    doSubmit(parsed.data satisfies TriageInput);
  }

  function handleConfirmAnyway() {
    if (!pendingConfirm) return;
    const input = pendingConfirm.input;
    setPendingConfirm(null);
    doSubmit(input);
  }

  const errorFor = (field: string) => fieldErrors[field];

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm space-y-6"
      noValidate
    >
      <fieldset className="space-y-4">
        <legend className="text-base font-bold text-slate-900 dark:text-slate-200 border-b border-slate-200 dark:border-slate-700 pb-2 w-full">
          Identitas &amp; Keluhan
        </legend>

        <div>
          <p id="pasien-field-label" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
            Pasien <span className="text-red-500">*</span>
          </p>

          {pasienTerpilih ? (
            <div className="flex items-center justify-between gap-2 px-3 py-2 border border-emerald-300 dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-950/30 rounded-lg text-sm">
              <span className="text-emerald-800 dark:text-emerald-300">
                ✓ <strong>{pasienTerpilih.nama}</strong>
                {pasienTerpilih.nik && (
                  <span className="text-emerald-600 dark:text-emerald-400"> &middot; NIK {pasienTerpilih.nik}</span>
                )}
              </span>
              <button
                type="button"
                onClick={() => setPasienTerpilih(null)}
                className="text-xs text-emerald-700 dark:text-emerald-400 hover:underline shrink-0"
              >
                Ganti
              </button>
            </div>
          ) : modePasienBaru ? (
            <div className="space-y-2">
              <input
                type="text"
                id="namaPasien"
                name="namaPasien"
                required
                aria-labelledby="pasien-field-label"
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm bg-white dark:bg-slate-900 dark:text-slate-200"
                placeholder="Nama pasien (belum terdaftar di sistem)"
              />
              <button
                type="button"
                onClick={() => setModePasienBaru(false)}
                className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
              >
                ← Kembali cari pasien terdaftar
              </button>
            </div>
          ) : (
            <div className="relative">
              <input
                type="text"
                value={pasienSearch}
                onChange={(e) => {
                  setPasienSearch(e.target.value);
                  setShowPasienDropdown(true);
                }}
                onFocus={() => setShowPasienDropdown(true)}
                onBlur={() => setTimeout(() => setShowPasienDropdown(false), 150)}
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm bg-white dark:bg-slate-900 dark:text-slate-200"
                placeholder="Cari nama pasien terdaftar…"
                aria-label="Cari pasien terdaftar"
              />
              {showPasienDropdown && (
                <div className="absolute z-10 mt-1 w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-lg max-h-56 overflow-y-auto">
                  {pasienCocok && pasienCocok.length > 0 ? (
                    pasienCocok.map((p) => (
                      <button
                        key={p.id}
                        type="button"
                        onMouseDown={() => {
                          setPasienTerpilih(p);
                          setPasienSearch("");
                          setShowPasienDropdown(false);
                        }}
                        className="block w-full text-left px-3 py-2 text-sm hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200"
                      >
                        {p.nama} {p.nik && <span className="text-slate-400 text-xs">&middot; {p.nik}</span>}
                      </button>
                    ))
                  ) : (
                    <p className="px-3 py-2 text-sm text-slate-400">Tidak ada pasien yang cocok.</p>
                  )}
                  <button
                    type="button"
                    onMouseDown={() => {
                      setModePasienBaru(true);
                      setShowPasienDropdown(false);
                    }}
                    className="block w-full text-left px-3 py-2 text-sm text-blue-600 dark:text-blue-400 border-t border-slate-100 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700"
                  >
                    + Pasien belum terdaftar (input manual)
                  </button>
                </div>
              )}
            </div>
          )}
          {errorFor("namaPasien") && <p className="text-xs text-red-600 mt-1">{errorFor("namaPasien")}</p>}
        </div>

        <Field label="Keluhan Utama" name="keluhanUtama" error={errorFor("keluhanUtama")} required>
          <input
            type="text"
            id="keluhanUtama"
            name="keluhanUtama"
            required
            className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm bg-white dark:bg-slate-900 dark:text-slate-200"
            placeholder="Contoh: Nyeri dada hebat"
          />
        </Field>

        <Field label="Uraian Gejala & Keluhan" name="gejala" error={errorFor("gejala")} required>
          <textarea
            id="gejala"
            name="gejala"
            rows={4}
            required
            className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm bg-white dark:bg-slate-900 dark:text-slate-200"
            placeholder="Jelaskan gejala yang dialami pasien secara rinci (minimal 10 karakter)"
          />
        </Field>

        <Field label="Riwayat Singkat" name="riwayatSingkat">
          <textarea
            id="riwayatSingkat"
            name="riwayatSingkat"
            rows={2}
            className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm bg-white dark:bg-slate-900 dark:text-slate-200"
            placeholder="Contoh: Riwayat hipertensi 5 tahun (opsional)"
          />
        </Field>
      </fieldset>

      <fieldset className="space-y-4">
        <legend className="text-base font-bold text-slate-900 dark:text-slate-200 border-b border-slate-200 dark:border-slate-700 pb-2 w-full">
          Tanda Vital
        </legend>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Field
            label="Tekanan Darah Sistolik (mmHg)"
            name="tekananDarahSistolik"
            error={errorFor("tandaVital.tekananDarahSistolik")}
            required
          >
            <input
              type="number"
              id="tekananDarahSistolik"
              name="tekananDarahSistolik"
              required
              className={numInputClass}
            />
          </Field>
          <Field
            label="Tekanan Darah Diastolik (mmHg)"
            name="tekananDarahDiastolik"
            error={errorFor("tandaVital.tekananDarahDiastolik")}
            required
          >
            <input
              type="number"
              id="tekananDarahDiastolik"
              name="tekananDarahDiastolik"
              required
              className={numInputClass}
            />
          </Field>
          <Field label="Suhu Tubuh (°C)" name="suhuTubuh" error={errorFor("tandaVital.suhuTubuh")} required>
            <input type="number" step="0.1" id="suhuTubuh" name="suhuTubuh" required className={numInputClass} />
          </Field>
          <Field label="Nadi (bpm)" name="nadiPerMenit" error={errorFor("tandaVital.nadiPerMenit")} required>
            <input type="number" id="nadiPerMenit" name="nadiPerMenit" required className={numInputClass} />
          </Field>
          <Field label="Laju Napas (/menit)" name="lajuNapas" error={errorFor("tandaVital.lajuNapas")} required>
            <input type="number" id="lajuNapas" name="lajuNapas" required className={numInputClass} />
          </Field>
          <Field
            label="Saturasi Oksigen (%)"
            name="saturasiOksigen"
            error={errorFor("tandaVital.saturasiOksigen")}
            required
          >
            <input
              type="number"
              step="0.1"
              id="saturasiOksigen"
              name="saturasiOksigen"
              required
              className={numInputClass}
            />
          </Field>
        </div>
      </fieldset>

      {pendingConfirm && (
        <div
          className="rounded-lg border border-amber-300 dark:border-amber-700 bg-amber-50 dark:bg-amber-950/30 p-4 space-y-3"
          role="alert"
          aria-labelledby="warning-heading"
        >
          <h3 id="warning-heading" className="font-semibold text-amber-900 dark:text-amber-300">
            ⚠ Beberapa tanda vital tidak lazim
          </h3>
          <ul className="text-sm text-amber-800 dark:text-amber-200 list-disc pl-5 space-y-1">
            {pendingConfirm.warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
          <p className="text-sm text-amber-800 dark:text-amber-200">
            Ini hanya peringatan — sistem tetap mengizinkan input jika memang sesuai kondisi pasien sesungguhnya.
            Pastikan dulu data yang dimasukkan sudah benar.
          </p>
          <div className="flex flex-wrap gap-3">
            <Button type="button" variant="destructive" onClick={handleConfirmAnyway} disabled={mutation.isPending}>
              {mutation.isPending ? "Memproses…" : "Ya, Data Sudah Benar — Lanjutkan"}
            </Button>
            <Button type="button" variant="outline" onClick={() => setPendingConfirm(null)}>
              Periksa Kembali
            </Button>
          </div>
        </div>
      )}

      <div>
        <Button type="submit" size="lg" disabled={mutation.isPending || !!pendingConfirm}>
          {mutation.isPending ? "Memproses klasifikasi AI…" : "Proses Klasifikasi AI"}
        </Button>
        <p className="text-sm mt-3" role="status" aria-live="polite">
          {mutation.isPending && (
            <span className="text-slate-500 dark:text-slate-400">
              Sistem sedang menganalisis gejala dan tanda vital. Mohon tunggu.
            </span>
          )}
          {mutation.isError && !(mutation.error instanceof ZodError) && (
            <span className="text-red-600">
              {mutation.error instanceof Error ? mutation.error.message : "Gagal memproses klasifikasi triase"}
            </span>
          )}
        </p>
      </div>
    </form>
  );
}

const numInputClass =
  "w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm bg-white dark:bg-slate-900 dark:text-slate-200";

function Field({
  label,
  name,
  error,
  required,
  children,
}: {
  label: string;
  name: string;
  error?: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label htmlFor={name} className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
        {label} {required && <span className="text-red-500">*</span>}
      </label>
      {children}
      {error && (
        <p className="text-xs text-red-600 mt-1" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
