import type { ReactNode } from "react";
import { LogoAplikasi } from "@/components/ui/logo";

/** Kerangka halaman Eir sesuai mockup SKPL Gambar 7.3: header gelap dan isi selebar layar ponsel. */
export function KerangkaEir({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col bg-white">
      <header className="bg-navy text-white">
        <div className="mx-auto flex max-w-xl items-center gap-3 px-4 py-2.5">
          <LogoAplikasi ukuran={34} />
          <div className="leading-tight">
            <p className="text-[17px] font-bold">Eir</p>
            <p className="text-[13px] text-navy-teks">Asisten anamnesis · SmartTriage AI</p>
          </div>
        </div>
      </header>
      <main className="mx-auto flex w-full max-w-xl flex-1 flex-col px-4 py-6">{children}</main>
    </div>
  );
}
