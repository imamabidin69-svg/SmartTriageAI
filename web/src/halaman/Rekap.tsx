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

/** Satu angka ringkasan. Empat angka dijajarkan dalam satu kotak bersekat, bukan empat kartu terpisah. */
function Angka({ label, nilai, keterangan }: { label: string; nilai: string; keterangan?: string }) {
  return (
    <div className="px-5 py-4">
      <p className="text-[15px] font-bold text-teks-2">{label}</p>
      <p className="mt-1.5 text-[32px] leading-tight font-bold text-teks">{nilai}</p>
      {keterangan ? <p className="mt-1 text-[13px] text-teks-3">{keterangan}</p> : null}
    </div>
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
          <h1 className="text-[26px] font-bold text-teks">Rekap</h1>
          <p className="mt-1 text-[15px] text-teks-2">
            Ringkasan penilaian prioritas ICU, koreksi dokter, observasi ulang, dan akurasi pemindaian. Tanggal
            mengikuti WIB.
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
          <p className="text-sm text-teks-2">
            Periode {tanggal(data.dari)} sampai {tanggal(data.sampai)}
          </p>
          <Card className="grid divide-y divide-garis-2 p-0 lg:grid-cols-4 lg:divide-x lg:divide-y-0">
            <Angka label="Penilaian tercatat" nilai={angka(data.total_triase)} />
            <Angka label="Dikoreksi dokter" nilai={persen(data.persen_koreksi)} keterangan="Dari semua penilaian" />
            <Angka label="Observasi ulang" nilai={angka(data.triase_ulang)} />
            <Angka
              label="Akurasi pemindaian layar"
              nilai={persen(data.akurasi_pemindaian)}
              keterangan={data.akurasi_pemindaian === null ? "Belum ada pemindaian yang dikonfirmasi" : undefined}
            />
          </Card>
          <Card className="overflow-x-auto">
            <JudulKartu
              judul="Per level prioritas"
              keterangan="Rata-rata waktu dari masuk ICU sampai tindakan pertama, menurut level penilaian terakhir."
            />
            <table className="w-full min-w-[420px] text-left text-[15px]">
              <thead className="border-b border-garis text-sm text-teks-2">
                <tr>
                  <th scope="col" className="py-2 font-bold">
                    Level
                  </th>
                  <th scope="col" className="py-2 text-right font-bold">
                    Jumlah penilaian
                  </th>
                  <th scope="col" className="py-2 text-right font-bold">
                    Rata-rata sampai tindakan
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-garis-2">
                {URUTAN_LEVEL.map((level) => {
                  const tunggu = data.rata_tunggu_menit[level];
                  return (
                    <tr key={level}>
                      <td className="py-3">
                        <RiskBadge level={level} />
                      </td>
                      <td className="py-3 text-right text-teks">{angka(data.per_level[level] ?? 0)}</td>
                      <td className="py-3 text-right text-teks">
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
