import { type FormEvent, useState } from "react";
import { bukaSesi } from "@/api/eir";
import { pesanError } from "@/api/klien";
import type { PengisiEir, SesiEirDibuat } from "@/api/tipe";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

const PILIHAN: { nilai: PengisiEir; label: string }[] = [
  { nilai: "keluarga", label: "Keluarga pasien" },
  { nilai: "pasien", label: "Pasien sendiri" },
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
        <h1 className="text-[26px] font-bold text-teks">Halo, saya Eir</h1>
        <p className="mt-3 text-base leading-relaxed text-teks">
          Pasien sedang dirawat di ICU dan belum bisa banyak ditanya. Saya akan menanyakan riwayat kesehatannya:
          kejadian sebelum masuk ICU, penyakit lama, obat rutin, dan alergi. Jawaban Anda membantu tim ICU merawat
          pasien.
        </p>
      </div>
      {/* Peringatan penting diberi garis tepi, bukan kotak berwarna, supaya terbaca tanpa terasa menakutkan. */}
      <div className="border-l-4 border-navy bg-latar px-4 py-3 text-[15px] leading-relaxed text-teks">
        Saya bukan dokter, jadi tidak memberi diagnosis atau kabar tentang kondisi pasien. Untuk itu, silakan bertanya
        langsung ke dokter atau perawat ICU. Nama dan NIK tidak dikirim ke layanan AI.
      </div>
      <fieldset>
        <legend className="mb-2 text-sm font-bold text-teks">Siapa yang mengisi?</legend>
        <div className="grid grid-cols-2 gap-3">
          {PILIHAN.map((pilihan) => (
            <label
              key={pilihan.nilai}
              className={`flex h-[52px] cursor-pointer items-center gap-2.5 rounded-md px-3 text-[15px] font-bold text-teks has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-biru ${
                pengisi === pilihan.nilai ? "border-2 border-biru bg-biru-muda" : "border border-garis-isian"
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
              <span
                aria-hidden
                className={`size-5 shrink-0 rounded-full ${
                  pengisi === pilihan.nilai ? "border-[6px] border-biru" : "border-2 border-garis-isian"
                }`}
              />
              {pilihan.label}
            </label>
          ))}
        </div>
        {galatField.pengisi ? <p className="mt-1 text-[13px] font-bold text-galat">{galatField.pengisi}</p> : null}
      </fieldset>
      <div>
        <label className="flex items-start gap-3 text-[15px] leading-relaxed text-teks">
          <input
            type="checkbox"
            checked={setuju}
            onChange={(e) => setSetuju(e.target.checked)}
            className="mt-0.5 size-5 shrink-0 accent-biru"
          />
          Saya mengerti penjelasan di atas dan setuju percakapan ini dicatat untuk perawat.
        </label>
        {galatField.setuju ? <p className="mt-1 text-[13px] font-bold text-galat">{galatField.setuju}</p> : null}
      </div>
      {galat ? <Alert jenis="galat">{galat}</Alert> : null}
      <Button type="submit" size="lg" className="w-full" disabled={mengirim}>
        {mengirim ? "Membuka percakapan..." : "Mulai percakapan"}
      </Button>
    </form>
  );
}
