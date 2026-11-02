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
  const warna =
    item.jenis === "sukses"
      ? "border-emerald-200 bg-emerald-50 text-emerald-900"
      : "border-red-200 bg-red-50 text-red-900";
  return (
    <div className={`flex items-start gap-3 rounded-lg border px-4 py-3 text-sm shadow-md ${warna}`}>
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
