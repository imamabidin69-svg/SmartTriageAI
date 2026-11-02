import type { HTMLAttributes, ReactNode } from "react";

// Kartu dari prototipe (components/ui/card.tsx): radius 12px, garis tipis, bayangan halus.
export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={`rounded-xl border border-slate-200 bg-white p-5 shadow-sm ${className ?? ""}`} {...props} />;
}

export function JudulKartu({ judul, keterangan }: { judul: string; keterangan?: ReactNode }) {
  return (
    <div className="mb-4">
      <h2 className="text-base font-semibold text-slate-900">{judul}</h2>
      {keterangan ? <p className="mt-1 text-sm text-slate-600">{keterangan}</p> : null}
    </div>
  );
}
