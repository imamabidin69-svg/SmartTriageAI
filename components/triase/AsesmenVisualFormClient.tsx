"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";
import { Button } from "@/components/ui/button";
import { useSubmitTriaseMutation } from "@/hooks/useTriaseQueries";
import { type TriageInput, TriageInputSchema } from "@/lib/schemas/triase.schema";

const OBSERVASI_OPTIONS = [
  { id: "tidak_respon", label: "Tidak berespon terhadap panggilan/rangsang nyeri" },
  { id: "napas_tidak_normal", label: "Pola napas tidak normal (cepat/lambat/tidak teratur)" },
  { id: "kulit_pucat", label: "Kulit pucat atau kebiruan (sianosis)" },
  { id: "luka_terlihat", label: "Terdapat luka/pendarahan yang terlihat" },
  { id: "kejang", label: "Kejang atau gerakan abnormal" },
  { id: "muntah", label: "Muntah atau terdapat cairan pada mulut" },
];

/**
 * AsesmenVisualFormClient - "use client": alur triase khusus pasien yang
 * TIDAK BISA menyampaikan keluhan sendiri (tidak sadar, tanpa pendamping).
 * Alih-alih uraian gejala bebas, Perawat mencatat observasi visual via
 * checklist + tanda vital — hasil observasi dirangkai otomatis menjadi
 * teks "gejala" lalu diproses lewat pipeline klasifikasi AI yang sama
 * dengan form triase biasa.
 */
export function AsesmenVisualFormClient() {
  const router = useRouter();
  const mutation = useSubmitTriaseMutation();
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setFieldErrors({});
    const fd = new FormData(e.currentTarget);
    const num = (name: string): number => Number(fd.get(name));

    const observasiTerpilih = OBSERVASI_OPTIONS.filter((o) => fd.get(o.id) === "on").map((o) => o.label);
    const catatanTambahan = fd.get("catatanTambahan")?.toString().trim();
    const gejala =
      (observasiTerpilih.length > 0
        ? `Pasien ditemukan tidak sadar. Observasi visual: ${observasiTerpilih.join("; ")}.`
        : "Pasien ditemukan tidak sadar tanpa observasi visual spesifik tercatat.") +
      (catatanTambahan ? ` Catatan tambahan: ${catatanTambahan}` : "");

    const raw = {
      idPasien: crypto.randomUUID(),
      namaPasien: fd.get("namaPasien")?.toString() || "Pasien Tidak Dikenal",
      keluhanUtama: "Ditemukan tidak sadar",
      gejala,
      tandaVital: {
        tekananDarahSistolik: num("tekananDarahSistolik"),
        tekananDarahDiastolik: num("tekananDarahDiastolik"),
        suhuTubuh: num("suhuTubuh"),
        nadiPerMenit: num("nadiPerMenit"),
        lajuNapas: num("lajuNapas"),
        saturasiOksigen: num("saturasiOksigen"),
      },
    };

    const parsed = TriageInputSchema.safeParse(raw);
    if (!parsed.success) {
      const errors: Record<string, string> = {};
      for (const issue of parsed.error.issues) errors[issue.path.join(".")] = issue.message;
      setFieldErrors(errors);
      return;
    }

    mutation.mutate(parsed.data satisfies TriageInput, {
      onSuccess: (record) => router.push(`/triase/${record.idTriase}`),
    });
  }

  const numInputClass =
    "w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-sm bg-white dark:bg-slate-900 dark:text-slate-200";

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm space-y-6"
      noValidate
    >
      <div>
        <label htmlFor="namaPasien" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
          Nama Pasien (jika diketahui)
        </label>
        <input
          type="text"
          id="namaPasien"
          name="namaPasien"
          placeholder="Kosongkan jika belum diketahui identitasnya"
          className={numInputClass}
        />
      </div>

      <fieldset className="space-y-3">
        <legend className="text-base font-bold text-slate-900 dark:text-slate-200 border-b border-slate-200 dark:border-slate-700 pb-2 w-full">
          Observasi Visual
        </legend>
        {OBSERVASI_OPTIONS.map((o) => (
          <label key={o.id} className="flex items-start gap-2 text-sm text-slate-700 dark:text-slate-300">
            <input type="checkbox" name={o.id} className="mt-0.5" />
            {o.label}
          </label>
        ))}
        <div>
          <label
            htmlFor="catatanTambahan"
            className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1 mt-2"
          >
            Catatan Tambahan
          </label>
          <textarea id="catatanTambahan" name="catatanTambahan" rows={2} className={numInputClass} />
        </div>
      </fieldset>

      <fieldset className="space-y-4">
        <legend className="text-base font-bold text-slate-900 dark:text-slate-200 border-b border-slate-200 dark:border-slate-700 pb-2 w-full">
          Tanda Vital
        </legend>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label
              htmlFor="tekananDarahSistolik"
              className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1"
            >
              Tekanan Darah Sistolik (mmHg) <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              id="tekananDarahSistolik"
              name="tekananDarahSistolik"
              required
              className={numInputClass}
            />
            {fieldErrors["tandaVital.tekananDarahSistolik"] && (
              <p className="text-xs text-red-600 mt-1">{fieldErrors["tandaVital.tekananDarahSistolik"]}</p>
            )}
          </div>
          <div>
            <label
              htmlFor="tekananDarahDiastolik"
              className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1"
            >
              Tekanan Darah Diastolik (mmHg) <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              id="tekananDarahDiastolik"
              name="tekananDarahDiastolik"
              required
              className={numInputClass}
            />
          </div>
          <div>
            <label htmlFor="suhuTubuh" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Suhu Tubuh (°C) <span className="text-red-500">*</span>
            </label>
            <input type="number" step="0.1" id="suhuTubuh" name="suhuTubuh" required className={numInputClass} />
          </div>
          <div>
            <label htmlFor="nadiPerMenit" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Nadi (bpm) <span className="text-red-500">*</span>
            </label>
            <input type="number" id="nadiPerMenit" name="nadiPerMenit" required className={numInputClass} />
          </div>
          <div>
            <label htmlFor="lajuNapas" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Laju Napas (/menit) <span className="text-red-500">*</span>
            </label>
            <input type="number" id="lajuNapas" name="lajuNapas" required className={numInputClass} />
          </div>
          <div>
            <label
              htmlFor="saturasiOksigen"
              className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1"
            >
              Saturasi Oksigen (%) <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              step="0.1"
              id="saturasiOksigen"
              name="saturasiOksigen"
              required
              className={numInputClass}
            />
          </div>
        </div>
      </fieldset>

      <Button type="submit" variant="destructive" size="lg" disabled={mutation.isPending}>
        {mutation.isPending ? "Memproses…" : "Proses Asesmen Darurat"}
      </Button>
    </form>
  );
}
