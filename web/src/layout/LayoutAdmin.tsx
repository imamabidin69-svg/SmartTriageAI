import { List, SignOut, X } from "@phosphor-icons/react";
import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router";
import { useKeluar } from "@/api/admin";
import type { Pengguna } from "@/api/tipe";
import { LogoAplikasi } from "@/components/ui/logo";
import { DaftarNotifikasi } from "@/components/ui/notifikasi";

const MENU = [
  { ke: "/staf", label: "Kelola Staf" },
  { ke: "/pengaturan", label: "Pengaturan" },
  { ke: "/rekap", label: "Rekap" },
  { ke: "/log-audit", label: "Log Audit" },
];

/** Menu di header: halaman aktif ditandai garis putih di bawah, bukan latar berbentuk pil. */
function kelasMenu({ isActive }: { isActive: boolean }) {
  return `relative flex h-full items-center px-3 text-[15px] font-bold ${
    isActive
      ? "text-white after:absolute after:inset-x-3 after:bottom-0 after:h-[3px] after:rounded-t-sm after:bg-white"
      : "text-navy-teks hover:text-white"
  }`;
}

/** Menu di layar sempit: daftar bertumpuk dengan garis kiri untuk halaman aktif. */
function kelasMenuPonsel({ isActive }: { isActive: boolean }) {
  return `block border-l-[3px] px-3 py-2.5 text-[15px] font-bold ${
    isActive ? "border-white text-white" : "border-transparent text-navy-teks hover:text-white"
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
      <header className="bg-navy text-white">
        <div className="mx-auto flex h-14 max-w-7xl items-stretch gap-7 px-4 md:px-8">
          <div className="flex items-center gap-2.5 text-base font-bold">
            <LogoAplikasi />
            SmartTriage AI
            <span className="ml-1 hidden border-l border-navy-garis pl-3 font-normal text-navy-teks sm:inline">
              Admin ICU
            </span>
          </div>
          <nav aria-label="Menu utama" className="hidden flex-1 md:block">
            <ul className="flex h-full gap-0.5">
              {MENU.map((item) => (
                <li key={item.ke} className="h-full">
                  <NavLink to={item.ke} className={kelasMenu}>
                    {item.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>
          <div className="ml-auto hidden items-center gap-4 text-[15px] md:flex">
            <NavLink to="/akun/password" className="font-bold text-white hover:underline" title="Ganti password">
              {pengguna.nama} · Admin ICU
            </NavLink>
            <button
              type="button"
              onClick={prosesKeluar}
              className="inline-flex items-center gap-1.5 border-l border-navy-garis pl-4 font-bold text-white hover:underline"
            >
              <SignOut size={18} aria-hidden /> Keluar
            </button>
          </div>
          <button
            type="button"
            className="ml-auto self-center rounded-md p-2 md:hidden"
            aria-expanded={menuTerbuka}
            aria-controls="menu-ponsel"
            aria-label={menuTerbuka ? "Tutup menu" : "Buka menu"}
            onClick={() => setMenuTerbuka((nilai) => !nilai)}
          >
            {menuTerbuka ? <X size={22} aria-hidden /> : <List size={22} aria-hidden />}
          </button>
        </div>
        {menuTerbuka ? (
          <nav id="menu-ponsel" aria-label="Menu utama" className="border-t border-navy-garis px-4 pb-4 md:hidden">
            <ul className="mt-2 space-y-0.5">
              {[...MENU, { ke: "/akun/password", label: "Ganti password" }].map((item) => (
                <li key={item.ke}>
                  <NavLink to={item.ke} className={kelasMenuPonsel} onClick={tutupMenu}>
                    {item.label}
                  </NavLink>
                </li>
              ))}
              <li>
                <button
                  type="button"
                  onClick={prosesKeluar}
                  className={`${kelasMenuPonsel({ isActive: false })} w-full text-left`}
                >
                  Keluar
                </button>
              </li>
            </ul>
          </nav>
        ) : null}
      </header>
      <main id="isi" className="mx-auto max-w-7xl px-4 py-7 md:px-8">
        <Outlet />
      </main>
      <DaftarNotifikasi />
    </div>
  );
}
