import { Microphone, PaperPlaneRight, Stop } from "@phosphor-icons/react";
import { type FormEvent, useEffect, useRef, useState } from "react";
import { kirimPesan, kirimSuara, selesaikan } from "@/api/eir";
import { ProblemError, pesanError } from "@/api/klien";
import type { BalasanEir, StatusSesiEir } from "@/api/tipe";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { dukungRekaman, useRekaman } from "@/lib/rekaman";
import type { PesanEir, SesiEirTersimpan } from "@/lib/sesiEir";

const PANJANG_MAKS = 1000;

interface PercakapanProps {
  sesi: SesiEirTersimpan;
  onUbah: (sesi: SesiEirTersimpan) => void;
}

interface Galat {
  pesan: string;
  jenis: "galat" | "peringatan";
}

/** Pertanyaan Eir di kiri dengan label nama, jawaban pasien di kanan berwarna biru tua (sama dengan aplikasi). */
function Gelembung({ pesan }: { pesan: PesanEir }) {
  const dariEir = pesan.peran === "eir";
  return (
    <li className={`flex flex-col ${dariEir ? "items-start" : "items-end"}`}>
      {dariEir ? (
        <span aria-hidden className="mb-1 text-[13px] font-bold text-teks-3">
          Eir
        </span>
      ) : null}
      <p
        className={`max-w-[88%] px-3.5 py-2.5 text-base leading-relaxed whitespace-pre-wrap ${
          dariEir
            ? "rounded-[2px_12px_12px_12px] bg-latar text-teks"
            : "rounded-[12px_2px_12px_12px] bg-navy text-white"
        }`}
      >
        <span className="sr-only">{dariEir ? "Eir: " : "Anda: "}</span>
        {pesan.teks}
      </p>
    </li>
  );
}

/** Halaman Percakapan Eir (SKPL Tabel 7.3 no. 2): pertanyaan lanjutan, kotak jawaban, dan arahan tanda bahaya. */
export function Percakapan({ sesi, onUbah }: PercakapanProps) {
  const [draf, setDraf] = useState("");
  const [mengirim, setMengirim] = useState(false);
  const [galat, setGalat] = useState<Galat>();
  const [ditutup, setDitutup] = useState(false);
  const akhir = useRef<HTMLDivElement>(null);
  const rekaman = useRekaman((blob, nama) => void kirimRekaman(blob, nama));

  const berjalan = sesi.status === "berjalan" && !ditutup;
  const terakhir = sesi.pesan.at(-1);
  // Pesan terakhir saat sesi berakhir ditampilkan sebagai kartu arahan, bukan gelembung biasa.
  const daftarGelembung = sesi.status === "berjalan" ? sesi.pesan : sesi.pesan.slice(0, -1);

  const jumlahPesan = sesi.pesan.length;
  useEffect(() => {
    // Setiap ada pesan baru, layar digeser ke kotak jawaban.
    if (jumlahPesan) akhir.current?.scrollIntoView?.({ block: "end" });
  }, [jumlahPesan]);

  function terapkan(balasan: BalasanEir, daftar: PesanEir[]) {
    onUbah({
      ...sesi,
      pesan: [...daftar, { peran: "eir", teks: balasan.pesan }],
      status: balasan.status,
      bolehSelesai: balasan.boleh_selesai,
      jumlahJawaban: balasan.jumlah_jawaban,
    });
  }

  /**
   * Menampilkan pesan error dan mengembalikan perubahan sesi yang perlu diterapkan. `tersimpan` true bila jawaban
   * tetap tercatat di server walau Eir tidak bisa membalas (503, keputusan E3).
   */
  function tangani(e: unknown): { tersimpan: boolean; ubah: Partial<SesiEirTersimpan> } {
    if (!(e instanceof ProblemError)) {
      setGalat({ pesan: pesanError(e), jenis: "galat" });
      return { tersimpan: false, ubah: {} };
    }
    if (e.status === 503) {
      setGalat({ pesan: pesanError(e), jenis: "peringatan" });
      return { tersimpan: true, ubah: {} };
    }
    let ubah: Partial<SesiEirTersimpan> = {};
    if (e.status === 401) setDitutup(true);
    if (e.status === 409) {
      const statusSesi = e.isi.status_sesi as StatusSesiEir | undefined;
      if (statusSesi) ubah = { status: statusSesi };
      else if (pesanError(e).includes("Selesai")) ubah = { bolehSelesai: true };
      else setDitutup(true);
    }
    setGalat({ pesan: e.pesanField.teks ?? e.pesanField.berkas ?? pesanError(e), jenis: "galat" });
    return { tersimpan: false, ubah };
  }

  async function kirimTeks(event: FormEvent) {
    event.preventDefault();
    const teks = draf.trim();
    if (!teks) {
      setGalat({ pesan: "Tulis jawaban terlebih dahulu.", jenis: "galat" });
      return;
    }
    const daftar: PesanEir[] = [...sesi.pesan, { peran: "pengisi", teks }];
    setGalat(undefined);
    setDraf("");
    setMengirim(true);
    onUbah({ ...sesi, pesan: daftar });
    try {
      terapkan(await kirimPesan(sesi.idSesi, sesi.tokenSesi, teks), daftar);
    } catch (e) {
      const { tersimpan, ubah } = tangani(e);
      if (tersimpan) {
        onUbah({ ...sesi, pesan: daftar, jumlahJawaban: sesi.jumlahJawaban + 1 });
      } else {
        // Jawaban tidak tersimpan: dikembalikan ke kotak supaya tidak perlu diketik ulang.
        onUbah({ ...sesi, ...ubah });
        setDraf(teks);
      }
    } finally {
      setMengirim(false);
    }
  }

  async function kirimRekaman(blob: Blob, nama: string) {
    setGalat(undefined);
    setMengirim(true);
    try {
      const balasan = await kirimSuara(sesi.idSesi, sesi.tokenSesi, blob, nama);
      terapkan(balasan, [...sesi.pesan, { peran: "pengisi", teks: balasan.transkripsi ?? "(rekaman suara)" }]);
    } catch (e) {
      const { ubah } = tangani(e);
      if (Object.keys(ubah).length) onUbah({ ...sesi, ...ubah });
    } finally {
      setMengirim(false);
    }
  }

  async function akhiri() {
    setGalat(undefined);
    setMengirim(true);
    try {
      terapkan(await selesaikan(sesi.idSesi, sesi.tokenSesi), sesi.pesan);
    } catch (e) {
      const { ubah } = tangani(e);
      if (Object.keys(ubah).length) onUbah({ ...sesi, ...ubah });
    } finally {
      setMengirim(false);
    }
  }

  return (
    <div className="flex flex-1 flex-col">
      <ol aria-label="Percakapan dengan Eir" aria-live="polite" className="flex-1 space-y-3.5">
        {daftarGelembung.map((pesan, urutan) => (
          // Urutan pesan tidak pernah berubah, jadi indeks aman dipakai sebagai kunci.
          // biome-ignore lint/suspicious/noArrayIndexKey: daftar hanya bertambah di akhir
          <Gelembung key={urutan} pesan={pesan} />
        ))}
      </ol>

      {sesi.status === "dihentikan" && terakhir ? (
        <div role="alert" className="mt-4 border border-l-4 border-garis border-l-kritis bg-white p-4 text-teks">
          <p className="text-base font-bold text-galat">Perlu dilihat perawat sekarang</p>
          <p className="mt-1 text-sm leading-relaxed">{terakhir.teks}</p>
        </div>
      ) : null}
      {sesi.status === "selesai" && terakhir ? (
        <div role="status" className="mt-4 border border-l-4 border-garis border-l-navy bg-white p-4 text-teks">
          <p className="text-base font-bold text-navy">Terima kasih</p>
          <p className="mt-1 text-sm leading-relaxed">{terakhir.teks}</p>
        </div>
      ) : null}

      <div ref={akhir} className="mt-4 space-y-3">
        {galat ? <Alert jenis={galat.jenis}>{galat.pesan}</Alert> : null}
        {rekaman.galat ? <Alert jenis="peringatan">{rekaman.galat}</Alert> : null}
        {berjalan && sesi.bolehSelesai ? (
          <Button variant="outline" className="w-full" onClick={akhiri} disabled={mengirim}>
            Selesai dan kirim ke perawat
          </Button>
        ) : null}
        <form onSubmit={kirimTeks} noValidate className="flex items-end gap-2">
          <div className="flex-1">
            <label htmlFor="jawaban-eir" className="mb-1 block text-sm font-bold text-teks">
              Jawaban Anda
            </label>
            <textarea
              id="jawaban-eir"
              rows={2}
              maxLength={PANJANG_MAKS}
              value={draf}
              disabled={!berjalan || rekaman.merekam}
              placeholder={
                sesi.status === "dihentikan"
                  ? "Percakapan dihentikan"
                  : sesi.status === "selesai"
                    ? "Percakapan selesai"
                    : ditutup
                      ? "Percakapan ditutup"
                      : undefined
              }
              onChange={(e) => setDraf(e.target.value)}
              className="block w-full resize-none rounded-md border border-garis-isian px-3 py-2 text-base focus:border-biru focus:outline-none focus:ring-1 focus:ring-biru disabled:bg-latar"
            />
          </div>
          {berjalan && dukungRekaman() ? (
            <Button
              variant="outline"
              size="lg"
              aria-label={rekaman.merekam ? "Berhenti merekam dan kirim" : "Jawab dengan suara"}
              onClick={rekaman.merekam ? rekaman.berhenti : rekaman.mulai}
              disabled={mengirim}
              className={rekaman.merekam ? "border-galat-garis text-galat" : undefined}
            >
              {rekaman.merekam ? <Stop size={20} aria-hidden /> : <Microphone size={20} aria-hidden />}
            </Button>
          ) : null}
          <Button
            type="submit"
            size="lg"
            aria-label="Kirim jawaban"
            disabled={!berjalan || mengirim || rekaman.merekam}
          >
            <PaperPlaneRight size={20} aria-hidden />
          </Button>
        </form>
        {rekaman.merekam ? (
          <p role="status" className="text-sm text-galat">
            Merekam... Tekan tombol berhenti bila sudah selesai bicara.
          </p>
        ) : null}
        {mengirim ? (
          <p role="status" className="text-sm text-teks-3">
            Eir sedang membaca jawaban...
          </p>
        ) : null}
      </div>
    </div>
  );
}
