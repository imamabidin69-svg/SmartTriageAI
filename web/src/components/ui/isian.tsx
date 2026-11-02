import { type InputHTMLAttributes, type ReactNode, type SelectHTMLAttributes, useId } from "react";

const kelasKontrol =
  "block w-full rounded-lg border bg-white px-3 py-2 text-sm text-slate-900 shadow-sm " +
  "focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-slate-100 disabled:text-slate-500 ";

function kelasGaris(galat?: string) {
  return galat ? "border-red-400" : "border-slate-300";
}

interface PropsDasar {
  label: string;
  galat?: string;
  petunjuk?: ReactNode;
}

function Bingkai({ id, label, galat, petunjuk, children }: PropsDasar & { id: string; children: ReactNode }) {
  return (
    <div>
      <label htmlFor={id} className="mb-1.5 block text-sm font-medium text-slate-800">
        {label}
      </label>
      {children}
      {petunjuk && !galat ? (
        <p id={`${id}-petunjuk`} className="mt-1 text-xs text-slate-500">
          {petunjuk}
        </p>
      ) : null}
      {galat ? (
        <p id={`${id}-galat`} className="mt-1 text-xs text-red-700">
          {galat}
        </p>
      ) : null}
    </div>
  );
}

function deskripsi(id: string, galat?: string, petunjuk?: ReactNode) {
  if (galat) return `${id}-galat`;
  return petunjuk ? `${id}-petunjuk` : undefined;
}

export function Isian({
  label,
  galat,
  petunjuk,
  className,
  ...props
}: PropsDasar & InputHTMLAttributes<HTMLInputElement>) {
  const id = useId();
  return (
    <Bingkai id={id} label={label} galat={galat} petunjuk={petunjuk}>
      <input
        id={id}
        aria-invalid={galat ? true : undefined}
        aria-describedby={deskripsi(id, galat, petunjuk)}
        className={`${kelasKontrol}${kelasGaris(galat)} ${className ?? ""}`}
        {...props}
      />
    </Bingkai>
  );
}

export function Pilihan({
  label,
  galat,
  petunjuk,
  className,
  children,
  ...props
}: PropsDasar & SelectHTMLAttributes<HTMLSelectElement>) {
  const id = useId();
  return (
    <Bingkai id={id} label={label} galat={galat} petunjuk={petunjuk}>
      <select
        id={id}
        aria-invalid={galat ? true : undefined}
        aria-describedby={deskripsi(id, galat, petunjuk)}
        className={`${kelasKontrol}${kelasGaris(galat)} ${className ?? ""}`}
        {...props}
      >
        {children}
      </select>
    </Bingkai>
  );
}
