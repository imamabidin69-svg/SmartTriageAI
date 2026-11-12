import { type ChangeEvent, type FormEvent, useEffect, useState } from "react";
import { z } from "zod";
import { unduhRekapCsv, useHealth, useKonfigurasi, useRekap, useSimpanKonfigurasi } from "@/api/admin";
import { ProblemError, pesanError } from "@/api/klien";
import type { Konfigurasi, KonfigurasiPatch } from "@/api/tipe";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, JudulKartu } from "@/components/ui/card";
import { Isian } from "@/components/ui/isian";
import { Memuat } from "@/components/ui/memuat";
import { angka, persen } from "@/lib/format";
import { useNotifikasi } from "@/lib/notifikasi";
import { galatZod } from "@/lib/validasi";

// Batas sama dengan KonfigurasiPatch di backend (skor NEWS2 1-20, interval observasi 1-1440 menit).
const SKOR_MAKSIMUM = 20;
const bulat = (label: string, maks: number) =>
  z.coerce
    .number({ message: `${label} harus berupa angka.` })
    .int(`${label} harus berupa bilangan bulat.`)
    .min(1, `${label} minimal 1.`)
    .max(maks, `${label} maksimal ${maks}.`);

const skema = z.object({
  batas_tunggu_kritis: bulat("Interval kritis", 1440),
  batas_tunggu_tinggi: bulat("Interval tinggi", 1440),
  batas_tunggu_sedang: bulat("Interval sedang", 1440),
  batas_tunggu_rendah: bulat("Interval rendah", 1440),
  ambang_kritis: bulat("Ambang kritis", SKOR_MAKSIMUM),
  ambang_tinggi: bulat("Ambang tinggi", SKOR_MAKSIMUM),
  ambang_sedang: bulat("Ambang sedang", SKOR_MAKSIMUM),
  ambang_keyakinan: z.preprocess(
    (nilai) => (typeof nilai === "string" ? nilai.replace(",", ".") : nilai),
    z.coerce
      .number({ message: "Ambang keyakinan harus berupa angka." })
      .min(0, "Ambang keyakinan minimal 0.")
      .max(1, "Ambang keyakinan maksimal 1."),
  ),
  versi_model: z.string().trim().min(1, "Versi model wajib diisi.").max(50, "Versi model maksimal 50 karakter."),
});

type Kolom = keyof z.input<typeof skema>;
type IsianForm = Record<Kolom, string>;

const KOLOM: Kolom[] = [
  "batas_tunggu_kritis",
  "batas_tunggu_tinggi",
  "batas_tunggu_sedang",
  "batas_tunggu_rendah",
  "ambang_kritis",
  "ambang_tinggi",
  "ambang_sedang",
  "ambang_keyakinan",
  "versi_model",
];

function keForm(konfigurasi: Konfigurasi): IsianForm {
  const hasil = {} as IsianForm;
  for (const kolom of KOLOM) {
    const nilai = konfigurasi[kolom];
    hasil[kolom] = kolom === "ambang_keyakinan" ? angka(Number(nilai), 2) : String(nilai);
  }
  return hasil;
}

/** Hanya kolom yang berubah yang dikirim, karena setiap perubahan dicatat per kolom di log audit. */
export function perubahanKonfigurasi(lama: Konfigurasi, baru: z.output<typeof skema>): KonfigurasiPatch {
  const patch: Record<string, unknown> = {};
  for (const kolom of KOLOM) {
    if (baru[kolom] !== lama[kolom]) patch[kolom] = baru[kolom];
  }
  return patch as KonfigurasiPatch;
}

function KartuRekap() {
  const rekap = useRekap();
  const tampilkan = useNotifikasi((s) => s.tampilkan);
  const [mengunduh, setMengunduh] = useState(false);

  async function ekspor() {
    setMengunduh(true);
    try {
      await unduhRekapCsv();
    } catch (galat) {
      tampilkan(pesanError(galat), "galat");
    } finally {
      setMengunduh(false);
    }
  }

  return (
    <Card>
      <JudulKartu judul="Rekap 7 hari terakhir" />
      {rekap.isPending ? <Memuat /> : null}
      {rekap.isError ? <Alert jenis="galat">{pesanError(rekap.error)}</Alert> : null}
      {rekap.data ? (
        <dl className="space-y-4">
          <div>
            <dt className="text-sm text-teks-2">Penilaian tercatat</dt>
            <dd className="text-3xl font-bold text-teks">{angka(rekap.data.total_triase)}</dd>
          </div>
          <div>
            <dt className="text-sm text-teks-2">Dikoreksi dokter</dt>
            <dd className="text-3xl font-bold text-teks">
              {angka(Math.round(((rekap.data.persen_koreksi ?? 0) * rekap.data.total_triase) / 100))}{" "}
              <span className="text-sm font-medium text-teks-3">({persen(rekap.data.persen_koreksi)})</span>
            </dd>
          </div>
          <div>
            <dt className="text-sm text-teks-2">Akurasi pemindaian layar</dt>
            <dd className="text-3xl font-bold text-teks">{persen(rekap.data.akurasi_pemindaian)}</dd>
          </div>
          <div>
            <dt className="text-sm text-teks-2">Observasi ulang</dt>
            <dd className="text-3xl font-bold text-teks">{angka(rekap.data.triase_ulang)}</dd>
          </div>
        </dl>
      ) : null}
      <Button variant="outline" className="mt-6" onClick={ekspor} disabled={mengunduh}>
        {mengunduh ? "Mengunduh..." : "Ekspor CSV"}
      </Button>
    </Card>
  );
}

export function HalamanPengaturan() {
  const konfigurasi = useKonfigurasi();
  const health = useHealth();
  const simpan = useSimpanKonfigurasi();
  const tampilkan = useNotifikasi((s) => s.tampilkan);
  const [isian, setIsian] = useState<IsianForm | null>(null);
  const [galatField, setGalatField] = useState<Record<string, string>>({});
  const [galat, setGalat] = useState<string>();

  useEffect(() => {
    if (konfigurasi.data) setIsian(keForm(konfigurasi.data));
  }, [konfigurasi.data]);

  if (konfigurasi.isPending) return <Memuat />;
  if (konfigurasi.isError) return <Alert jenis="galat">{pesanError(konfigurasi.error)}</Alert>;
  if (!isian) return null;
  const lama = konfigurasi.data;

  function ubah(kolom: Kolom, nilai: string) {
    setIsian((sebelum) => (sebelum ? { ...sebelum, [kolom]: nilai } : sebelum));
  }

  function kirim(event: FormEvent) {
    event.preventDefault();
    setGalat(undefined);
    const hasil = skema.safeParse(isian);
    if (!hasil.success) {
      setGalatField(galatZod(hasil.error));
      return;
    }
    setGalatField({});
    const patch = perubahanKonfigurasi(lama, hasil.data);
    if (!Object.keys(patch).length) {
      setGalat("Belum ada pengaturan yang diubah.");
      return;
    }
    simpan.mutate(patch, {
      onSuccess: () => tampilkan("Pengaturan tersimpan dan tercatat di log audit."),
      onError: (e) => {
        if (e instanceof ProblemError) setGalatField(e.pesanField);
        setGalat(pesanError(e));
      },
    });
  }

  const props = (kolom: Kolom) => ({
    value: isian[kolom],
    onChange: (e: ChangeEvent<HTMLInputElement>) => ubah(kolom, e.target.value),
    galat: galatField[kolom],
    inputMode: "numeric" as const,
  });

  const statusPembaca = health.data?.komponen.pembaca_layar;

  return (
    <div>
      <h1 className="text-[26px] font-bold text-teks">Pengaturan Penilaian ICU</h1>
      <p className="mt-1 mb-6 text-sm text-teks-2">
        Perubahan berlaku untuk observasi berikutnya dan tercatat di log audit.
      </p>
      <div className="grid gap-6 lg:grid-cols-[1fr_20rem]">
        <form onSubmit={kirim} noValidate className="space-y-6">
          {galat ? <Alert jenis="galat">{galat}</Alert> : null}
          <Card>
            <JudulKartu
              judul="Interval observasi per level"
              keterangan="Lewat interval ini, pasien ditandai observasi terlambat. Sesuaikan dengan SOP ICU."
            />
            <div className="grid gap-4 sm:grid-cols-4">
              <Isian label="Kritis (menit)" {...props("batas_tunggu_kritis")} />
              <Isian label="Tinggi (menit)" {...props("batas_tunggu_tinggi")} />
              <Isian label="Sedang (menit)" {...props("batas_tunggu_sedang")} />
              <Isian label="Rendah (menit)" {...props("batas_tunggu_rendah")} />
            </div>
          </Card>
          <Card>
            <JudulKartu
              judul="Ambang skor NEWS2"
              keterangan="Skor minimal untuk tiap level. Satu parameter bernilai 3 selalu minimal Sedang. Bawaan NEWS2: 7, 5, 3."
            />
            <div className="grid gap-4 sm:grid-cols-3">
              <Isian label="Kritis (skor)" {...props("ambang_kritis")} />
              <Isian label="Tinggi (skor)" {...props("ambang_tinggi")} />
              <Isian label="Sedang (skor)" {...props("ambang_sedang")} />
            </div>
          </Card>
          <Card>
            <JudulKartu judul="Pemindaian layar alat dan model" />
            <div className="grid gap-4 sm:grid-cols-3">
              <Isian
                label="Ambang keyakinan"
                {...props("ambang_keyakinan")}
                inputMode="decimal"
                petunjuk="0 sampai 1, misalnya 0,85."
              />
              <Isian
                label="Model perburukan aktif"
                {...props("versi_model")}
                inputMode="text"
                petunjuk={`Model yang dimuat: ${lama.versi_model_termuat ?? "tidak ada (NEWS2 saja)"}`}
              />
              {/* Keputusan W6: status model pembaca layar hanya ditampilkan dari health check. */}
              <Isian
                label="Model pembaca layar"
                value={statusPembaca === undefined ? "Memeriksa..." : statusPembaca === "ok" ? "Aktif" : "Tidak aktif"}
                readOnly
                disabled
                petunjuk={statusPembaca === "gagal" ? "Kolom hasil pemindaian diisi manual oleh perawat." : undefined}
              />
            </div>
          </Card>
          <Button type="submit" disabled={simpan.isPending}>
            {simpan.isPending ? "Menyimpan..." : "Simpan perubahan"}
          </Button>
        </form>
        <aside>
          <KartuRekap />
        </aside>
      </div>
    </div>
  );
}
