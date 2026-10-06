"use client";

import { ArrowLeft, Check, Plus, Warning } from "@phosphor-icons/react";
import { useRouter } from "next/navigation";
import { type FormEvent, type KeyboardEvent, useRef, useState } from "react";
import { flushSync } from "react-dom";
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
  const [opsiAktif, setOpsiAktif] = useState(-1);
  const cariPasienRef = useRef<HTMLInputElement>(null);
  const gantiPasienRef = useRef<HTMLButtonElement>(null);
  const namaManualRef = useRef<HTMLInputElement>(null);

  const pasienCocok =
    (pasienSearch.trim().length > 0
      ? pasienList?.filter((p) => p.nama.toLowerCase().includes(pasienSearch.trim().toLowerCase())).slice(0, 6)
      : pasienList?.slice(0, 6)) ?? [];
  // Opsi terakhir di listbox selalu "Pasien belum terdaftar (input manual)".
  const indexOpsiManual = pasienCocok.length;
  const jumlahOpsi = pasienCocok.length + 1;

  function tutupDaftarPasien() {
    setShowPasienDropdown(false);
    setOpsiAktif(-1);
  }

  function pilihPasien(pasien: Pasien) {
    flushSync(() => {
      setPasienTerpilih(pasien);
      setPasienSearch("");
      tutupDaftarPasien();
    });
    gantiPasienRef.current?.focus();
  }

  function pilihInputManual() {
    flushSync(() => {
      setModePasienBaru(true);
      tutupDaftarPasien();
    });
    namaManualRef.current?.focus();
  }

  function kembaliKePencarian() {
    flushSync(() => {
      setPasienTerpilih(null);
      setModePasienBaru(false);
    });
    cariPasienRef.current?.focus();
  }

  // Pola combobox WAI-ARIA: panah memindah opsi aktif, Enter memilih, Esc menutup daftar.
  function handleCariPasienKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      const turun = e.key === "ArrowDown";
      if (!showPasienDropdown) {
        setShowPasienDropdown(true);
        setOpsiAktif(turun ? 0 : jumlahOpsi - 1);
        return;
      }
      setOpsiAktif((i) => (turun ? (i + 1) % jumlahOpsi : i <= 0 ? jumlahOpsi - 1 : i - 1));
    } else if (e.key === "Enter" && showPasienDropdown && opsiAktif >= 0) {
      e.preventDefault();
      if (opsiAktif === indexOpsiManual) {
        pilihInputManual();
      } else {
        const pasien = pasienCocok[opsiAktif];
        if (pasien) pilihPasien(pasien);
      }
    } else if (e.key === "Escape" && showPasienDropdown) {
      e.preventDefault();
      tutupDaftarPasien();
    }
  }

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
            Pasien{" "}
            <span className="text-red-600 dark:text-red-400" aria-hidden="true">
              *
            </span>
          </p>

          {pasienTerpilih ? (
            <div className="flex items-center justify-between gap-2 px-3 py-2 border border-emerald-300 dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-950/30 rounded-lg text-sm">
              <span className="flex items-center gap-1.5 text-emerald-800 dark:text-emerald-300">
                <Check size={16} aria-hidden="true" className="shrink-0" />
                <strong>{pasienTerpilih.nama}</strong>
                {pasienTerpilih.nik && (
                  <span className="tabular-nums text-emerald-700 dark:text-emerald-400">
                    {" "}
                    &middot; NIK {pasienTerpilih.nik}
                  </span>
                )}
              </span>
              <button
                ref={gantiPasienRef}
                type="button"
                onClick={kembaliKePencarian}
                aria-label={`Ganti pasien terpilih (${pasienTerpilih.nama})`}
                className="text-xs text-emerald-700 dark:text-emerald-400 hover:underline shrink-0"
              >
                Ganti
              </button>
            </div>
          ) : modePasienBaru ? (
            <div className="space-y-2">
              <input
                ref={namaManualRef}
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
                onClick={kembaliKePencarian}
                className="inline-flex items-center gap-1.5 text-xs text-blue-600 dark:text-blue-400 hover:underline"
              >
                <ArrowLeft size={14} aria-hidden="true" />
                Kembali cari pasien terdaftar
              </button>
            </div>
          ) : (
            <div className="relative">
              <input
                ref={cariPasienRef}
                id="cari-pasien"
                type="text"
                role="combobox"
                aria-labelledby="pasien-field-label"
                aria-autocomplete="list"
                aria-expanded={showPasienDropdown}
                aria-controls="pasien-listbox"
                aria-activedescendant={showPasienDropdown && opsiAktif >= 0 ? `pasien-opsi-${opsiAktif}` : undefined}
                autoComplete="off"
                value={pasienSearch}
                onChange={(e) => {
                  setPasienSearch(e.target.value);
                  setShowPasienDropdown(true);
                  setOpsiAktif(-1);
                }}
                onFocus={() => setShowPasienDropdown(true)}
                onBlur={tutupDaftarPasien}
                onKeyDown={handleCariPasienKeyDown}
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm bg-white dark:bg-slate-900 dark:text-slate-200"
                placeholder="Cari nama pasien terdaftar…"
              />
              {showPasienDropdown && (
                <div className="enter-fade absolute z-(--z-dropdown) mt-1 w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-lg max-h-56 overflow-y-auto">
                  {pasienCocok.length === 0 && (
                    <p className="px-3 py-2 text-sm text-slate-500 dark:text-slate-400">Tidak ada pasien yang cocok.</p>
                  )}
                  <div id="pasien-listbox" role="listbox" aria-labelledby="pasien-field-label">
                    {pasienCocok.map((p, i) => (
                      // Keyboard ditangani input combobox lewat aria-activedescendant (pola WAI-ARIA).
                      // biome-ignore lint/a11y/useKeyWithClickEvents: opsi dipilih lewat keyboard dari input combobox
                      <div
                        key={p.id}
                        id={`pasien-opsi-${i}`}
                        role="option"
                        tabIndex={-1}
                        aria-selected={opsiAktif === i}
                        onMouseDown={(e) => e.preventDefault()}
                        onClick={() => pilihPasien(p)}
                        className={`cursor-pointer px-3 py-2 text-sm ${
                          opsiAktif === i
                            ? "bg-blue-50 text-blue-800 dark:bg-slate-700 dark:text-white"
                            : "text-slate-800 hover:bg-slate-50 dark:text-slate-200 dark:hover:bg-slate-700"
                        }`}
                      >
                        {p.nama}{" "}
                        {p.nik && (
                          <span className="text-xs tabular-nums text-slate-600 dark:text-slate-300">
                            &middot; {p.nik}
                          </span>
                        )}
                      </div>
                    ))}
                    {/* biome-ignore lint/a11y/useKeyWithClickEvents: opsi dipilih lewat keyboard dari input combobox */}
                    <div
                      id={`pasien-opsi-${indexOpsiManual}`}
                      role="option"
                      tabIndex={-1}
                      aria-selected={opsiAktif === indexOpsiManual}
                      onMouseDown={(e) => e.preventDefault()}
                      onClick={pilihInputManual}
                      className={`flex cursor-pointer items-center gap-1.5 px-3 py-2 text-sm border-t border-slate-100 dark:border-slate-700 ${
                        opsiAktif === indexOpsiManual
                          ? "bg-blue-50 text-blue-800 dark:bg-slate-700 dark:text-white"
                          : "text-blue-600 hover:bg-slate-50 dark:text-blue-400 dark:hover:bg-slate-700"
                      }`}
                    >
                      <Plus size={16} aria-hidden="true" className="shrink-0" />
                      Pasien belum terdaftar (input manual)
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
          {errorFor("namaPasien") && (
            <p className="text-xs text-red-600 dark:text-red-400 mt-1" role="alert">
              {errorFor("namaPasien")}
            </p>
          )}
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
          <h2
            id="warning-heading"
            className="flex items-center gap-1.5 font-semibold text-amber-900 dark:text-amber-300"
          >
            <Warning size={18} aria-hidden="true" className="shrink-0" />
            Beberapa tanda vital tidak lazim
          </h2>
          <ul className="text-sm text-amber-800 dark:text-amber-200 list-disc pl-5 space-y-1">
            {pendingConfirm.warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
          <p className="text-sm text-amber-800 dark:text-amber-200">
            Ini hanya peringatan. Sistem tetap mengizinkan input jika memang sesuai kondisi pasien sesungguhnya.
            Pastikan dulu data yang dimasukkan sudah benar.
          </p>
          <div className="flex flex-wrap gap-3">
            <Button type="button" variant="destructive" onClick={handleConfirmAnyway} disabled={mutation.isPending}>
              {mutation.isPending ? "Memproses…" : "Ya, Data Sudah Benar"}
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
            <span className="text-red-600 dark:text-red-400">
              {mutation.error instanceof Error ? mutation.error.message : "Gagal memproses klasifikasi triase"}
            </span>
          )}
        </p>
      </div>
    </form>
  );
}

const numInputClass =
  "w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm tabular-nums bg-white dark:bg-slate-900 dark:text-slate-200";

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
        {label}{" "}
        {required && (
          <span className="text-red-600 dark:text-red-400" aria-hidden="true">
            *
          </span>
        )}
      </label>
      {children}
      {error && (
        <p className="text-xs text-red-600 dark:text-red-400 mt-1" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
