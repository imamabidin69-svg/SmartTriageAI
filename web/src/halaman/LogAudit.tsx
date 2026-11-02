import { ArrowRight } from "@phosphor-icons/react";
import { type FormEvent, useState } from "react";
import { type FilterLogAudit, useLogAudit, useStaf } from "@/api/admin";
import { pesanError } from "@/api/klien";
import type { AksiAudit } from "@/api/tipe";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Isian, Pilihan } from "@/components/ui/isian";
import { Memuat } from "@/components/ui/memuat";
import { RiskBadge } from "@/components/ui/risk-badge";
import { waktuWib } from "@/lib/format";
import { LABEL_AKSI, LABEL_PERAN } from "@/lib/label";

const FILTER_KOSONG = { dari: "", sampai: "", aksi: "", id_aktor: "" };

function keFilter(isian: typeof FILTER_KOSONG): FilterLogAudit {
  return {
    dari: isian.dari || undefined,
    sampai: isian.sampai || undefined,
    aksi: (isian.aksi || undefined) as AksiAudit | undefined,
    id_aktor: isian.id_aktor || undefined,
  };
}

export function HalamanLogAudit() {
  const [isian, setIsian] = useState(FILTER_KOSONG);
  const [filter, setFilter] = useState<FilterLogAudit>({});
  const [galat, setGalat] = useState<string>();
  const log = useLogAudit(filter);
  const staf = useStaf();

  function terapkan(event: FormEvent) {
    event.preventDefault();
    if (isian.dari && isian.sampai && isian.dari > isian.sampai) {
      setGalat("Tanggal awal tidak boleh melewati tanggal akhir.");
      return;
    }
    setGalat(undefined);
    setFilter(keFilter(isian));
  }

  function aturUlang() {
    setIsian(FILTER_KOSONG);
    setGalat(undefined);
    setFilter({});
  }

  const baris = log.data?.pages.flatMap((halaman) => halaman.items) ?? [];

  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-900">Log Audit</h1>
      <p className="mt-1 mb-6 text-sm text-slate-600">
        Jejak validasi, koreksi, perubahan pengaturan, dan pengelolaan staf. Log tidak bisa diubah atau dihapus.
      </p>

      <Card className="mb-6">
        <form onSubmit={terapkan} noValidate className="grid items-end gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <Isian
            label="Dari tanggal"
            type="date"
            value={isian.dari}
            onChange={(e) => setIsian({ ...isian, dari: e.target.value })}
          />
          <Isian
            label="Sampai tanggal"
            type="date"
            value={isian.sampai}
            onChange={(e) => setIsian({ ...isian, sampai: e.target.value })}
          />
          <Pilihan label="Aksi" value={isian.aksi} onChange={(e) => setIsian({ ...isian, aksi: e.target.value })}>
            <option value="">Semua aksi</option>
            {Object.entries(LABEL_AKSI).map(([nilai, label]) => (
              <option key={nilai} value={nilai}>
                {label}
              </option>
            ))}
          </Pilihan>
          <Pilihan
            label="Pelaku"
            value={isian.id_aktor}
            onChange={(e) => setIsian({ ...isian, id_aktor: e.target.value })}
          >
            <option value="">Semua staf</option>
            {(staf.data?.items ?? []).map((s) => (
              <option key={s.id_pengguna} value={s.id_pengguna}>
                {s.nama} ({LABEL_PERAN[s.peran]})
              </option>
            ))}
          </Pilihan>
          <div className="flex gap-2">
            <Button type="submit">Terapkan</Button>
            <Button variant="outline" onClick={aturUlang}>
              Reset
            </Button>
          </div>
        </form>
        {galat ? (
          <div className="mt-4">
            <Alert jenis="galat">{galat}</Alert>
          </div>
        ) : null}
      </Card>

      <Card className="overflow-x-auto p-0">
        {log.isPending ? <Memuat /> : null}
        {log.isError ? (
          <div className="p-5">
            <Alert jenis="galat">{pesanError(log.error)}</Alert>
          </div>
        ) : null}
        {log.data && !baris.length ? (
          <p className="p-8 text-center text-sm text-slate-600">
            Tidak ada catatan untuk filter ini. Ubah atau reset filter.
          </p>
        ) : null}
        {baris.length ? (
          <table className="w-full min-w-[860px] text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50 text-xs text-slate-600 uppercase">
              <tr>
                <th scope="col" className="px-4 py-3 font-semibold">
                  Waktu
                </th>
                <th scope="col" className="px-4 py-3 font-semibold">
                  Aksi
                </th>
                <th scope="col" className="px-4 py-3 font-semibold">
                  Pelaku
                </th>
                <th scope="col" className="px-4 py-3 font-semibold">
                  Perubahan level
                </th>
                <th scope="col" className="px-4 py-3 font-semibold">
                  Catatan
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {baris.map((item) => (
                <tr key={item.id_log} className="align-top">
                  <td className="px-4 py-3 whitespace-nowrap text-slate-700">{waktuWib(item.waktu)}</td>
                  <td className="px-4 py-3 font-medium text-slate-900">{LABEL_AKSI[item.aksi]}</td>
                  <td className="px-4 py-3 text-slate-700">{item.aktor.nama}</td>
                  <td className="px-4 py-3">
                    {item.level_sebelum && item.level_sesudah ? (
                      <span className="inline-flex items-center gap-2">
                        <RiskBadge level={item.level_sebelum} />
                        <ArrowRight size={14} aria-label="menjadi" />
                        <RiskBadge level={item.level_sesudah} />
                      </span>
                    ) : (
                      <span className="text-slate-400">-</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-slate-700">{item.catatan ?? "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : null}
      </Card>
      {log.hasNextPage ? (
        <div className="mt-4 flex justify-center">
          <Button variant="outline" onClick={() => log.fetchNextPage()} disabled={log.isFetchingNextPage}>
            {log.isFetchingNextPage ? "Memuat..." : "Muat catatan sebelumnya"}
          </Button>
        </div>
      ) : null}
    </div>
  );
}
