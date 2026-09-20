"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { useAiConfigQuery, useUpdateAiConfigMutation } from "@/hooks/useAiConfigQueries";
import { UpdateAiConfigPayloadSchema } from "@/lib/schemas/ai-config.schema";

/**
 * KonfigurasiAiFormClient - "use client": form ini SEKARANG benar-benar
 * memengaruhi lib/classify.ts (via lib/data/ai-config-store.ts), bukan
 * cuma tampilan seperti sebelumnya. Ambang batas Kritis > Tinggi > Sedang
 * divalidasi berurutan (Zod refine) sebelum disimpan.
 */
export function KonfigurasiAiFormClient() {
  const { data: config, isPending } = useAiConfigQuery();
  const mutation = useUpdateAiConfigMutation();

  const [versiModel, setVersiModel] = useState("v1.2.0-rule-based");
  const [ambangKritis, setAmbangKritis] = useState(6);
  const [ambangTinggi, setAmbangTinggi] = useState(4);
  const [ambangSedang, setAmbangSedang] = useState(2);
  const [wajibDpj, setWajibDpj] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  // Sinkronkan form dengan data yang berhasil di-fetch dari server.
  useEffect(() => {
    if (!config) return;
    setVersiModel(config.versiModel);
    setAmbangKritis(config.ambangKritis);
    setAmbangTinggi(config.ambangTinggi);
    setAmbangSedang(config.ambangSedang);
    setWajibDpj(config.wajibkanValidasiDpjUntukKritis);
  }, [config]);

  function handleSave() {
    setError(null);
    setSaved(false);
    const parsed = UpdateAiConfigPayloadSchema.safeParse({
      versiModel,
      ambangKritis,
      ambangTinggi,
      ambangSedang,
      wajibkanValidasiDpjUntukKritis: wajibDpj,
    });
    if (!parsed.success) {
      setError(parsed.error.issues[0]?.message ?? "Konfigurasi tidak valid.");
      return;
    }
    mutation.mutate(parsed.data, {
      onSuccess: () => {
        setSaved(true);
        setTimeout(() => setSaved(false), 2500);
      },
      onError: (err) => setError(err instanceof Error ? err.message : "Gagal menyimpan konfigurasi."),
    });
  }

  if (isPending) {
    return <p className="text-sm text-slate-500 dark:text-slate-400">Memuat konfigurasi…</p>;
  }

  return (
    <div className="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm space-y-6 max-w-2xl">
      <div>
        <label htmlFor="versiModel" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
          Versi Model Aktif
        </label>
        <select
          id="versiModel"
          value={versiModel}
          onChange={(e) => setVersiModel(e.target.value)}
          className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-sm bg-white dark:bg-slate-900 dark:text-slate-200"
        >
          <option value="v1.2.0-rule-based">v1.2.0 — Rule-based (aktif)</option>
          <option value="v2.0.0-beta-ml">v2.0.0-beta — Machine Learning (belum tersedia)</option>
        </select>
      </div>

      <div className="border-t border-slate-200 dark:border-slate-700 pt-4">
        <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Ambang Batas Skor Klasifikasi</p>
        <p className="text-xs text-slate-400 mb-3">
          Perubahan di sini langsung memengaruhi klasifikasi triase berikutnya di seluruh faskes.
        </p>
        <div className="space-y-4">
          {[
            { label: "Kritis", value: ambangKritis, setValue: setAmbangKritis, color: "accent-red-600" },
            { label: "Tinggi", value: ambangTinggi, setValue: setAmbangTinggi, color: "accent-orange-600" },
            { label: "Sedang", value: ambangSedang, setValue: setAmbangSedang, color: "accent-amber-600" },
          ].map((item) => (
            <div key={item.label}>
              <div className="flex items-center justify-between text-sm mb-1">
                <label htmlFor={`ambang-${item.label}`} className="text-slate-700 dark:text-slate-300">
                  {item.label}
                </label>
                <span className="font-mono text-slate-500 dark:text-slate-400">{item.value}</span>
              </div>
              <input
                id={`ambang-${item.label}`}
                type="range"
                min={1}
                max={12}
                value={item.value}
                onChange={(e) => item.setValue(Number(e.target.value))}
                className={`w-full ${item.color}`}
              />
            </div>
          ))}
        </div>
      </div>

      <div className="border-t border-slate-200 dark:border-slate-700 pt-4 space-y-2">
        <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
          <input type="checkbox" checked={wajibDpj} onChange={(e) => setWajibDpj(e.target.checked)} />
          Wajibkan validasi DPJ untuk kasus kritis
        </label>
        <p className="text-xs text-slate-400 ml-6">
          Nonaktifkan kotak ini akan membuka jalur Perawat menyetujui sendiri kasus kritis — hanya untuk skenario
          pengujian, tidak disarankan pada operasional sungguhan.
        </p>
      </div>

      {error && (
        <p className="text-sm text-red-600 dark:text-red-400" role="alert">
          {error}
        </p>
      )}
      {saved && (
        <p className="text-sm text-emerald-700 dark:text-emerald-400" role="status">
          Konfigurasi tersimpan dan langsung berlaku.
        </p>
      )}

      <Button type="button" onClick={handleSave} disabled={mutation.isPending}>
        {mutation.isPending ? "Menyimpan…" : "Simpan Konfigurasi"}
      </Button>
    </div>
  );
}
