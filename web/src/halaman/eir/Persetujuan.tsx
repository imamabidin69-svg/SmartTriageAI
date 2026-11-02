import { type FormEvent, useState } from "react";
import { bukaSesi } from "@/api/eir";
import { pesanError } from "@/api/klien";
import type { PengisiEir, SesiEirDibuat } from "@/api/tipe";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

const PILIHAN: { nilai: PengisiEir; label: string }[] = [
  { nilai: "pasien", label: "Saya pasien" },
  { nilai: "keluarga", label: "Keluarga pendamping" },
];

interface PersetujuanProps {
  token: string;
  onMulai: (sesi: SesiEirDibuat) => void;
}

/** Halaman Persetujuan Eir (SKPL Tabel 7.3 no. 1): penjelasan singkat, pilihan pengisi, dan persetujuan. */
export function Persetujuan({ token, onMulai }: PersetujuanProps) {
  const [pengisi, setPengisi] = useState<PengisiEir>();
  const [setuju, setSetuju] = useState(false);
  const [galatField, setGalatField] = useState<{ pengisi?: string; setuju?: string }>({});
  const [galat, setGalat] = useState<string>();
  const [mengirim, setMengirim] = useState(false);

  async function kirim(event: FormEvent) {
    event.preventDefault();
    const periksa = {
      pengisi: pengisi ? undefined : "Pilih siapa yang mengisi.",
      setuju: setuju ? undefined : "Centang persetujuan untuk memulai percakapan.",
    };
    setGalatField(periksa);
    if (!pengisi || !setuju) return;
    setGalat(undefined);
    setMengirim(true);
    try {
      onMulai(await bukaSesi(token, pengisi));
    } catch (e) {
      setGalat(pesanError(e));
    } finally {
      setMengirim(false);
    }
  }

  return (
    <form onSubmit={kirim} noValidate className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Halo, saya Eir</h1>
        <p className="mt-3 text-base leading-relaxed text-slate-700">
          Sambil menunggu dipanggil, saya akan menanyakan beberapa hal tentang keluhan. Jawaban Anda membantu perawat
          dan dokter memahami kondisi pasien lebih cepat.
        </p>
      </div>
      <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm leading-relaxed text-slate-700">
        Saya bukan dokter dan tidak memberi diagnosis. Bila keluhan memburuk, langsung temui perawat. Nama dan NIK tidak
        dikirim ke layanan AI.
      </div>
      <fieldset>
        <legend className="mb-2 text-sm font-semibold text-slate-800">Siapa yang mengisi?</legend>
        <div className="grid grid-cols-2 gap-3">
          {PILIHAN.map((pilihan) => (
            <label
              key={pilihan.nilai}
              className={`flex h-12 cursor-pointer items-center justify-center rounded-lg border text-sm font-semibold has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-blue-500 ${
                pengisi === pilihan.nilai
                  ? "border-blue-600 bg-blue-50 text-blue-700"
                  : "border-slate-300 text-slate-800"
              }`}
            >
              <input
                type="radio"
                name="pengisi"
                value={pilihan.nilai}
                checked={pengisi === pilihan.nilai}
                onChange={() => setPengisi(pilihan.nilai)}
                className="sr-only"
              />
              {pilihan.label}
            </label>
          ))}
        </div>
        {galatField.pengisi ? <p className="mt-1 text-xs text-red-700">{galatField.pengisi}</p> : null}
      </fieldset>
      <div>
        <label className="flex items-start gap-3 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={setuju}
            onChange={(e) => setSetuju(e.target.checked)}
            className="mt-0.5 size-5 shrink-0 accent-blue-600"
          />
          Saya mengerti penjelasan di atas dan setuju percakapan ini dicatat untuk perawat.
        </label>
        {galatField.setuju ? <p className="mt-1 text-xs text-red-700">{galatField.setuju}</p> : null}
      </div>
      {galat ? <Alert jenis="galat">{galat}</Alert> : null}
      <Button type="submit" size="lg" className="w-full" disabled={mengirim}>
        {mengirim ? "Membuka percakapan..." : "Mulai percakapan"}
      </Button>
    </form>
  );
}
