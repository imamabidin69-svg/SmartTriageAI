import type { HTMLAttributes, ReactNode } from "react";

// Kotak putih datar: sudut 6px dan garis tipis, tanpa bayangan (panduan gaya tahap 6D).
export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  // "p-0" menggantikan padding bawaan. Dua kelas padding sekaligus tidak bisa diandalkan karena urutannya
  // ditentukan stylesheet Tailwind, bukan urutan di className.
  const padding = className?.split(/\s+/).includes("p-0") ? "" : "p-5";
  return <div className={`rounded-md border border-garis bg-white ${padding} ${className ?? ""}`} {...props} />;
}

export function JudulKartu({ judul, keterangan }: { judul: string; keterangan?: ReactNode }) {
  return (
    <div className="mb-4">
      <h2 className="text-base font-bold text-teks">{judul}</h2>
      {keterangan ? <p className="mt-1 text-sm text-teks-3">{keterangan}</p> : null}
    </div>
  );
}
