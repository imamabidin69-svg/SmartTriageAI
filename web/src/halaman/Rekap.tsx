import { type FormEvent, useState } from "react";
import { unduhRekapCsv, useRekap } from "@/api/admin";
import { pesanError } from "@/api/klien";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, JudulKartu } from "@/components/ui/card";
import { Isian } from "@/components/ui/isian";
import { Memuat } from "@/components/ui/memuat";
import { RiskBadge } from "@/components/ui/risk-badge";
import { angka, persen, selisihHari, tanggal, tanggalWib } from "@/lib/format";
import { URUTAN_LEVEL } from "@/lib/label";
import { useNotifikasi } from "@/lib/notifikasi";

// Sama dengan batas RekapQuery di backend.
const RENTANG_MAKSIMUM_HARI = 366;

export function periksaRentang(dari: string, sampai: string): string | undefined {
  if (!dari || !sampai) return "Isi tanggal awal dan tanggal akhir.";
  if (dari > sampai) return "Tanggal awal tidak boleh melewati tanggal akhir.";
  if (selisihHari(dari, sampai) + 1 > RENTANG_MAKSIMUM_HARI) return "Rentang tanggal maksimal 366 hari.";
  return undefined;
}

function Angka({ label, nilai, keterangan }: { label: string; nilai: string; keterangan?: string }) {
  return (
    <Card>
      <p className="text-sm text-slate-600">{label}</p>
      <p className="mt-1 text-3xl font-semibold text-slate-900">{nilai}</p>
      {keterangan ? <p className="mt-1 text-xs text-slate-500">{keterangan}</p> : null}
    </Card>
  );
}

export function HalamanRekap() {
  const [isian, setIsian] = useState({ dari: tanggalWib(-6), sampai: tanggalWib() });
  const [rentang, setRentang] = useState(isian);
  const [galat, setGalat] = useState<string>();
  const [mengunduh, setMengunduh] = useState(false);
  const rekap = useRekap(rentang.dari, rentang.sampai);
  const tampilkan = useNotifikasi((s) => s.tampilkan);

  function terapkan(event: FormEvent) {
    event.preventDefault();
    const pesan = periksaRentang(isian.dari, isian.sampai);
    setGalat(pesan);
    if (!pesan) setRentang(isian);
  }

  async function ekspor() {
    setMengunduh(true);
    try {
      await unduhRekapCsv(rentang.dari, rentang.sampai);
    } catch (e) {
      tampilkan(pesanError(e), "galat");
    } finally {
      setMengunduh(false);
    }
  }

  const data = rekap.data;

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Rekap</h1>
          <p className="mt-1 text-sm text-slate-600">
            Ringkasan triase, koreksi dokter, triase ulang, dan akurasi pemindaian. Tanggal mengikuti WIB.
          </p>
        </div>
        <Button variant="outline" onClick={ekspor} disabled={mengunduh || !data}>
          {mengunduh ? "Mengunduh..." : "Ekspor CSV"}
        </Button>
      </div>

      <Card className="mb-6">
        <form onSubmit={terapkan} noValidate className="grid items-end gap-4 sm:grid-cols-[1fr_1fr_auto]">
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
          <Button type="submit">Tampilkan rekap</Button>
        </form>
        {galat ? (
          <div className="mt-4">
            <Alert jenis="galat">{galat}</Alert>
          </div>
        ) : null}
      </Card>

      {rekap.isPending ? <Memuat /> : null}
      {rekap.isError ? <Alert jenis="galat">{pesanError(rekap.error)}</Alert> : null}
      {data ? (
        <div className="space-y-6">
          <p className="text-sm text-slate-600">
            Periode {tanggal(data.dari)} sampai {tanggal(data.sampai)}
          </p>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Angka label="Triase tercatat" nilai={angka(data.total_triase)} />
            <Angka label="Dikoreksi dokter" nilai={persen(data.persen_koreksi)} keterangan="Dari semua triase" />
            <Angka label="Triase ulang" nilai={angka(data.triase_ulang)} />
            <Angka
              label="Akurasi pemindaian layar"
              nilai={persen(data.akurasi_pemindaian)}
              keterangan={data.akurasi_pemindaian === null ? "Belum ada pemindaian yang dikonfirmasi" : undefined}
            />
          </div>
          <Card className="overflow-x-auto">
            <JudulKartu
              judul="Per risk level"
              keterangan="Rata-rata tunggu dihitung dari datang sampai ditangani dokter, menurut level triase terakhir."
            />
            <table className="w-full min-w-[420px] text-left text-sm">
              <thead className="border-b border-slate-200 text-xs text-slate-600 uppercase">
                <tr>
                  <th scope="col" className="py-2 font-semibold">
                    Risk level
                  </th>
                  <th scope="col" className="py-2 text-right font-semibold">
                    Jumlah triase
                  </th>
                  <th scope="col" className="py-2 text-right font-semibold">
                    Rata-rata tunggu
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {URUTAN_LEVEL.map((level) => {
                  const tunggu = data.rata_tunggu_menit[level];
                  return (
                    <tr key={level}>
                      <td className="py-3">
                        <RiskBadge level={level} />
                      </td>
                      <td className="py-3 text-right text-slate-900">{angka(data.per_level[level] ?? 0)}</td>
                      <td className="py-3 text-right text-slate-900">
                        {tunggu === null || tunggu === undefined ? "-" : `${angka(tunggu, 1)} menit`}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Card>
        </div>
      ) : null}
    </div>
  );
}
