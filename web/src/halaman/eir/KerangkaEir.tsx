import type { ReactNode } from "react";

/** Kerangka halaman Eir sesuai mockup SKPL Gambar 7.3: header gelap dan isi selebar layar ponsel. */
export function KerangkaEir({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col bg-white">
      <header className="bg-slate-800 text-white">
        <div className="mx-auto flex h-14 max-w-xl items-center gap-3 px-4 font-semibold">
          <span aria-hidden className="size-7 rounded-md bg-blue-600" />
          Eir · SmartTriage AI
        </div>
      </header>
      <main className="mx-auto flex w-full max-w-xl flex-1 flex-col px-4 py-6">{children}</main>
    </div>
  );
}
