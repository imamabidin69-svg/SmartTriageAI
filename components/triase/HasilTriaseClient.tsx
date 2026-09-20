"use client";

import { type FormEvent, useState } from "react";
import { Button } from "@/components/ui/button";
import { RiskBadge } from "@/components/ui/risk-badge";
import { useSubmitValidasiMutation, useTriaseDetailQuery } from "@/hooks/useTriaseQueries";
import { type RiskLevel, RiskLevelSchema, type Session } from "@/lib/schemas/triase.schema";

const STATUS_LABEL: Record<string, string> = {
  disetujui: "Disetujui",
  dikoreksi: "Dikoreksi oleh DPJ",
  menunggu_review_dokter: "Menunggu Review Dokter",
};

/**
 * HasilTriaseClient - "use client": useTriaseDetailQuery (Server State,
 * TanStack Query) + useSubmitValidasiMutation. `allowedOverride` diteruskan
 * sebagai PROP dari Server Component pembungkus (bukan dibaca ulang dari
 * cookie di klien) — cookie httpOnly memang sengaja tidak bisa dibaca
 * document.cookie di browser, jadi keputusan RBAC untuk tampilan tetap
 * berasal dari server, walau penegakannya yang sesungguhnya ada di Route
 * Handler (defense-in-depth, Modul 6 Bab G).
 */
export function HasilTriaseClient({
  idTriase,
  currentUserId,
  allowedOverride,
}: {
  idTriase: string;
  currentUserId: Session["userId"];
  allowedOverride: boolean;
}) {
  const { data: record, isPending, isError, error } = useTriaseDetailQuery(idTriase);
  const validasiMutation = useSubmitValidasiMutation();
  const [showKoreksiForm, setShowKoreksiForm] = useState(false);
  const [catatanError, setCatatanError] = useState<string | null>(null);
  const [showAjukanReviewForm, setShowAjukanReviewForm] = useState(false);
  const [catatanReviewError, setCatatanReviewError] = useState<string | null>(null);

  if (isPending) {
    return (
      <div className="py-12 text-center text-slate-500 dark:text-slate-400" role="status">
        Memuat data triase…
      </div>
    );
  }
  if (isError || !record) {
    return (
      <div
        className="rounded-lg border border-red-200 bg-red-50 dark:bg-red-950/30 p-4 text-red-800 dark:text-red-300"
        role="alert"
      >
        {error instanceof Error ? error.message : "Data triase tidak ditemukan."}
      </div>
    );
  }

  function handleSetujui() {
    validasiMutation.mutate({ aksi: "setujui", idTriase, idUserValidator: currentUserId });
  }

  function handleKoreksiSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setCatatanError(null);
    const fd = new FormData(e.currentTarget);
    const riskParsed = RiskLevelSchema.safeParse(fd.get("riskLevelBaru"));
    const catatan = fd.get("catatanKoreksi")?.toString() ?? "";

    if (catatan.trim().length < 5) {
      setCatatanError("Catatan koreksi wajib diisi minimal 5 karakter.");
      return;
    }
    if (!riskParsed.success) {
      setCatatanError("Risk level baru tidak valid.");
      return;
    }

    validasiMutation.mutate(
      {
        aksi: "koreksi",
        idTriase,
        idUserValidator: currentUserId,
        riskLevelBaru: riskParsed.data,
        catatanKoreksi: catatan,
      },
      { onError: (err) => setCatatanError(err instanceof Error ? err.message : "Gagal menyimpan koreksi.") },
    );
  }

  function handleAjukanReviewSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setCatatanReviewError(null);
    const fd = new FormData(e.currentTarget);
    const catatan = fd.get("catatanPerawat")?.toString() ?? "";

    if (catatan.trim().length < 5) {
      setCatatanReviewError("Catatan wajib diisi minimal 5 karakter — jelaskan alasan tidak sepakat.");
      return;
    }

    validasiMutation.mutate(
      { aksi: "ajukan_review", idTriase, idUserValidator: currentUserId, catatanPerawat: catatan },
      { onError: (err) => setCatatanReviewError(err instanceof Error ? err.message : "Gagal mengajukan review.") },
    );
  }

  const isFinalized = record.statusValidasi === "disetujui" || record.statusValidasi === "dikoreksi";
  const isMenungguReviewDokter = record.statusValidasi === "menunggu_review_dokter";
  const isKritisTanpaWewenang = record.riskLevel === "kritis" && !allowedOverride;

  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
        <h2 className="text-xl font-bold text-slate-900 dark:text-slate-200">{record.namaPasien}</h2>
        <RiskBadge level={record.riskLevel} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <section
          aria-labelledby="gejala-heading"
          className="rounded-lg border border-slate-200 dark:border-slate-700 p-4"
        >
          <h3 id="gejala-heading" className="font-semibold text-slate-800 dark:text-slate-200 mb-2">
            Gejala &amp; Keluhan
          </h3>
          <p className="text-sm text-slate-600 dark:text-slate-400 mb-1">
            <strong>Keluhan utama:</strong> {record.keluhanUtama}
          </p>
          <p className="text-sm text-slate-600 dark:text-slate-400">{record.gejala}</p>
        </section>
        <section
          aria-labelledby="vital-heading"
          className="rounded-lg border border-slate-200 dark:border-slate-700 p-4"
        >
          <h3 id="vital-heading" className="font-semibold text-slate-800 dark:text-slate-200 mb-2">
            Tanda Vital
          </h3>
          <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm text-slate-600 dark:text-slate-400">
            <dt>Tekanan darah</dt>
            <dd>
              {record.tandaVital.tekananDarahSistolik}/{record.tandaVital.tekananDarahDiastolik} mmHg
            </dd>
            <dt>Suhu tubuh</dt>
            <dd>{record.tandaVital.suhuTubuh} °C</dd>
            <dt>Nadi</dt>
            <dd>{record.tandaVital.nadiPerMenit} bpm</dd>
            <dt>Laju napas</dt>
            <dd>{record.tandaVital.lajuNapas} /menit</dd>
            <dt>Saturasi O₂</dt>
            <dd>{record.tandaVital.saturasiOksigen}%</dd>
          </dl>
        </section>
      </div>

      <section
        aria-labelledby="rujukan-heading"
        className="rounded-lg border border-indigo-200 dark:border-indigo-900 bg-indigo-50 dark:bg-indigo-950/30 p-4 mb-6"
      >
        <h3 id="rujukan-heading" className="font-semibold text-indigo-900 dark:text-indigo-300 mb-2">
          Rujukan Poli &amp; Dokter
        </h3>
        <dl className="grid grid-cols-1 sm:grid-cols-3 gap-x-4 gap-y-1 text-sm text-indigo-900 dark:text-indigo-200">
          <dt className="font-medium">Poli tujuan</dt>
          <dd className="sm:col-span-2">{record.poliTujuan}</dd>
          <dt className="font-medium">Dokter</dt>
          <dd className="sm:col-span-2">{record.dokterRujukan.nama}</dd>
          <dt className="font-medium">Jenis dokter</dt>
          <dd className="sm:col-span-2">
            {record.dokterRujukan.jenis === "spesialis"
              ? `Dokter Spesialis${record.dokterRujukan.spesialisasi ? ` (${record.dokterRujukan.spesialisasi})` : ""}`
              : "Dokter Umum"}
          </dd>
        </dl>
      </section>

      <section
        aria-labelledby="explain-heading"
        className="rounded-lg border border-blue-200 dark:border-blue-900 bg-blue-50 dark:bg-blue-950/30 p-4 mb-6"
      >
        <h3 id="explain-heading" className="font-semibold text-blue-900 dark:text-blue-300 mb-2">
          Penjelasan Rekomendasi AI (Explainable AI)
        </h3>
        <p className="text-sm text-blue-900 dark:text-blue-200">{record.penjelasanAi}</p>
      </section>

      {isMenungguReviewDokter && (
        <p className="text-xs text-amber-700 dark:text-amber-400 mb-3" role="note">
          Perawat telah mengajukan kasus ini untuk ditinjau ulang oleh Dokter Penanggung Jawab.
        </p>
      )}

      {isFinalized ? (
        <p className="text-sm font-medium text-slate-700 dark:text-slate-300" role="status">
          Status validasi: {STATUS_LABEL[record.statusValidasi] ?? record.statusValidasi}.
        </p>
      ) : isMenungguReviewDokter && !allowedOverride ? (
        <p className="text-sm font-medium text-slate-700 dark:text-slate-300" role="status">
          Menunggu review Dokter Penanggung Jawab (DPJ). Tidak ada aksi lebih lanjut yang diperlukan dari Anda saat ini.
        </p>
      ) : (
        <div className="space-y-4">
          <div className="flex flex-wrap gap-3">
            {!isKritisTanpaWewenang && (
              <Button type="button" onClick={handleSetujui} disabled={validasiMutation.isPending}>
                {validasiMutation.isPending ? "Menyimpan…" : "Setujui Hasil Triase"}
              </Button>
            )}

            {!allowedOverride && record.riskLevel !== "kritis" && record.statusValidasi === "menunggu" && (
              <Button type="button" variant="outline" onClick={() => setShowAjukanReviewForm((s) => !s)}>
                Tidak Setuju, Ajukan Review Dokter
              </Button>
            )}

            {isKritisTanpaWewenang && (
              <p className="w-full text-xs text-amber-700 dark:text-amber-400" role="note">
                Kasus dengan risk level KRITIS wajib ditangani Dokter Penanggung Jawab (DPJ) — Anda tidak berwenang
                menyetujui sendiri untuk kasus kritis.
              </p>
            )}

            {allowedOverride && (
              <Button type="button" variant="destructive" onClick={() => setShowKoreksiForm((s) => !s)}>
                Koreksi Risk Level (DPJ)
              </Button>
            )}
          </div>

          {allowedOverride && showKoreksiForm && (
            <form
              onSubmit={handleKoreksiSubmit}
              className="rounded-lg border border-red-200 dark:border-red-900 p-4 space-y-3"
              aria-label="Form koreksi risk level oleh DPJ"
            >
              <div>
                <label
                  htmlFor="riskLevelBaru"
                  className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1"
                >
                  Risk Level Baru
                </label>
                <select
                  id="riskLevelBaru"
                  name="riskLevelBaru"
                  defaultValue="kritis"
                  className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-slate-900 dark:text-slate-200"
                >
                  {(["rendah", "sedang", "tinggi", "kritis"] satisfies RiskLevel[]).map((lvl) => (
                    <option key={lvl} value={lvl}>
                      {lvl[0]?.toUpperCase() + lvl.slice(1)}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label
                  htmlFor="catatanKoreksi"
                  className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1"
                >
                  Catatan Koreksi <span className="text-red-500">*</span>
                </label>
                <textarea
                  id="catatanKoreksi"
                  name="catatanKoreksi"
                  rows={3}
                  required
                  className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-slate-900 dark:text-slate-200"
                  aria-describedby="catatan-error"
                />
                {catatanError && (
                  <p id="catatan-error" className="text-xs text-red-600 mt-1" role="alert">
                    {catatanError}
                  </p>
                )}
              </div>
              <Button type="submit" variant="destructive" disabled={validasiMutation.isPending}>
                {validasiMutation.isPending ? "Menyimpan…" : "Simpan Koreksi"}
              </Button>
            </form>
          )}

          {!allowedOverride && showAjukanReviewForm && (
            <form
              onSubmit={handleAjukanReviewSubmit}
              className="rounded-lg border border-amber-300 dark:border-amber-800 p-4 space-y-3"
              aria-label="Form ajukan review ke Dokter Penanggung Jawab"
            >
              <div>
                <label
                  htmlFor="catatanPerawat"
                  className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1"
                >
                  Alasan Tidak Sepakat <span className="text-red-500">*</span>
                </label>
                <textarea
                  id="catatanPerawat"
                  name="catatanPerawat"
                  rows={3}
                  required
                  className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-slate-900 dark:text-slate-200"
                  aria-describedby="catatan-review-error"
                  placeholder="Jelaskan mengapa Anda menilai rekomendasi AI perlu ditinjau ulang oleh dokter"
                />
                {catatanReviewError && (
                  <p id="catatan-review-error" className="text-xs text-red-600 mt-1" role="alert">
                    {catatanReviewError}
                  </p>
                )}
              </div>
              <Button type="submit" variant="outline" disabled={validasiMutation.isPending}>
                {validasiMutation.isPending ? "Mengirim…" : "Ajukan ke Dokter Penanggung Jawab"}
              </Button>
            </form>
          )}
        </div>
      )}
    </>
  );
}
