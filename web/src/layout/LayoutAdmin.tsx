import { List, SignOut, X } from "@phosphor-icons/react";
import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router";
import { useKeluar } from "@/api/admin";
import type { Pengguna } from "@/api/tipe";
import { DaftarNotifikasi } from "@/components/ui/notifikasi";

const MENU = [
  { ke: "/staf", label: "Kelola Staf" },
  { ke: "/pengaturan", label: "Pengaturan" },
  { ke: "/rekap", label: "Rekap" },
  { ke: "/log-audit", label: "Log Audit" },
];

function kelasMenu({ isActive }: { isActive: boolean }) {
  return `block rounded-lg px-3 py-2 text-sm font-medium ${
    isActive ? "bg-slate-700 text-white" : "text-slate-300 hover:bg-slate-700/60 hover:text-white"
  }`;
}

/** Kerangka halaman admin sesuai mockup SKPL Gambar 7.2: header gelap berisi menu dan nama pengguna. */
export function LayoutAdmin({ pengguna }: { pengguna: Pengguna }) {
  const [menuTerbuka, setMenuTerbuka] = useState(false);
  const keluar = useKeluar();
  const navigasi = useNavigate();

  const tutupMenu = () => setMenuTerbuka(false);
  const prosesKeluar = () => keluar.mutate(undefined, { onSettled: () => navigasi("/login", { replace: true }) });

  return (
    <div className="min-h-screen">
      <a
        href="#isi"
        className="sr-only focus:not-sr-only focus:absolute focus:m-2 focus:rounded focus:bg-white focus:p-2"
      >
        Lewati ke isi
      </a>
      <header className="bg-slate-800 text-white">
        <div className="mx-auto flex h-16 max-w-7xl items-center gap-6 px-4">
          <div className="flex items-center gap-3 font-semibold">
            <span aria-hidden className="size-7 rounded-md bg-blue-600" />
            SmartTriage AI
          </div>
          <nav aria-label="Menu utama" className="hidden flex-1 md:block">
            <ul className="flex gap-1">
              {MENU.map((item) => (
                <li key={item.ke}>
                  <NavLink to={item.ke} className={kelasMenu}>
                    {item.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>
          <div className="ml-auto hidden items-center gap-3 text-sm md:flex">
            <NavLink to="/akun/password" className="text-slate-300 hover:text-white">
              {pengguna.nama} · Admin IGD
            </NavLink>
            <button
              type="button"
              onClick={prosesKeluar}
              className="inline-flex items-center gap-1 rounded-lg px-2 py-1.5 text-slate-300 hover:bg-slate-700 hover:text-white"
            >
              <SignOut size={18} aria-hidden /> Keluar
            </button>
          </div>
          <button
            type="button"
            className="ml-auto rounded-lg p-2 md:hidden"
            aria-expanded={menuTerbuka}
            aria-controls="menu-ponsel"
            aria-label={menuTerbuka ? "Tutup menu" : "Buka menu"}
            onClick={() => setMenuTerbuka((nilai) => !nilai)}
          >
            {menuTerbuka ? <X size={22} aria-hidden /> : <List size={22} aria-hidden />}
          </button>
        </div>
        {menuTerbuka ? (
          <nav id="menu-ponsel" aria-label="Menu utama" className="border-t border-slate-700 px-4 pb-4 md:hidden">
            <ul className="mt-2 space-y-1">
              {[...MENU, { ke: "/akun/password", label: "Ganti password" }].map((item) => (
                <li key={item.ke}>
                  <NavLink to={item.ke} className={kelasMenu} onClick={tutupMenu}>
                    {item.label}
                  </NavLink>
                </li>
              ))}
              <li>
                <button type="button" onClick={prosesKeluar} className={kelasMenu({ isActive: false })}>
                  Keluar
                </button>
              </li>
            </ul>
          </nav>
        ) : null}
      </header>
      <main id="isi" className="mx-auto max-w-7xl px-4 py-8">
        <Outlet />
      </main>
      <DaftarNotifikasi />
    </div>
  );
}
