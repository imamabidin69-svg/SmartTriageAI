import { type InputHTMLAttributes, type ReactNode, type SelectHTMLAttributes, useId } from "react";

// Batas isian #7D8896 (kontras 3,6:1 terhadap putih), fokus berupa garis biru tebal tanpa bayangan.
const kelasKontrol =
  "block h-10 w-full rounded-md border bg-white px-3 text-[15px] text-teks " +
  "focus:border-biru focus:outline-none focus:ring-1 focus:ring-biru disabled:bg-latar disabled:text-teks-3 ";

function kelasGaris(galat?: string) {
  return galat ? "border-galat ring-1 ring-galat" : "border-garis-isian";
}

interface PropsDasar {
  label: string;
  galat?: string;
  petunjuk?: ReactNode;
}

function Bingkai({ id, label, galat, petunjuk, children }: PropsDasar & { id: string; children: ReactNode }) {
  return (
    <div>
      <label htmlFor={id} className="mb-1.5 block text-sm font-bold text-teks">
        {label}
      </label>
      {children}
      {petunjuk && !galat ? (
        <p id={`${id}-petunjuk`} className="mt-1 text-[13px] text-teks-3">
          {petunjuk}
        </p>
      ) : null}
      {galat ? (
        <p id={`${id}-galat`} className="mt-1 text-[13px] font-bold text-galat">
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
