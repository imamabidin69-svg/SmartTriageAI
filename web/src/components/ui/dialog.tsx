import { type ReactNode, useEffect, useId, useRef } from "react";

interface DialogProps {
  terbuka: boolean;
  judul: string;
  onTutup: () => void;
  children: ReactNode;
}

/** Dialog modal memakai elemen <dialog>: fokus terkunci di dalam dan tombol Escape menutupnya. */
export function Dialog({ terbuka, judul, onTutup, children }: DialogProps) {
  const ref = useRef<HTMLDialogElement>(null);
  const idJudul = useId();

  useEffect(() => {
    const elemen = ref.current;
    if (!elemen) return;
    if (terbuka && !elemen.open) elemen.showModal();
    if (!terbuka && elemen.open) elemen.close();
  }, [terbuka]);

  return (
    <dialog
      ref={ref}
      aria-labelledby={idJudul}
      onCancel={(event) => {
        // Escape: penutupan diatur lewat state supaya dialog lain yang dibuka sesudahnya tidak ikut tertutup.
        event.preventDefault();
        onTutup();
      }}
      className="m-auto w-[calc(100%-2rem)] max-w-lg rounded-md border border-garis bg-white p-6 shadow-xl"
    >
      {terbuka ? (
        <>
          <h2 id={idJudul} className="mb-4 text-xl font-bold text-teks">
            {judul}
          </h2>
          {children}
        </>
      ) : null}
    </dialog>
  );
}
