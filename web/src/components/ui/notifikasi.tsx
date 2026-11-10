import { X } from "@phosphor-icons/react";
import { useEffect } from "react";
import { type Notifikasi, useNotifikasi } from "@/lib/notifikasi";

const LAMA_TAMPIL_MS = 5000;

function ItemNotifikasi({ item }: { item: Notifikasi }) {
  const tutup = useNotifikasi((state) => state.tutup);
  useEffect(() => {
    const waktu = setTimeout(() => tutup(item.id), LAMA_TAMPIL_MS);
    return () => clearTimeout(waktu);
  }, [item.id, tutup]);
  // Seperti snackbar di aplikasi mobile: gelap untuk keberhasilan, merah untuk galat.
  const warna = item.jenis === "sukses" ? "bg-teks" : "bg-galat";
  return (
    <div className={`flex items-start gap-3 rounded-md px-4 py-3 text-[15px] text-white shadow-lg ${warna}`}>
      <p className="flex-1">{item.pesan}</p>
      <button type="button" onClick={() => tutup(item.id)} aria-label="Tutup notifikasi" className="text-current">
        <X size={16} aria-hidden />
      </button>
    </div>
  );
}

export function DaftarNotifikasi() {
  const daftar = useNotifikasi((state) => state.daftar);
  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed top-20 right-4 z-50 flex w-80 max-w-[calc(100%-2rem)] flex-col gap-2"
    >
      {daftar.map((item) => (
        <ItemNotifikasi key={item.id} item={item} />
      ))}
    </div>
  );
}
