import type { ReactNode } from "react";

/** Kerangka halaman status (404, error) yang memakai monogram merek yang sama dengan halaman login. */
export function StatusPage({ title, children }: { title: string; children: ReactNode }) {
  return (
    <main
      id="konten-utama"
      tabIndex={-1}
      className="min-h-dvh flex items-center justify-center px-4 bg-slate-50 dark:bg-slate-900 focus:outline-none"
    >
      <div className="w-full max-w-md text-center">
        <div
          className="w-14 h-14 bg-blue-600 rounded-xl mx-auto flex items-center justify-center font-bold text-2xl text-white mb-3"
          aria-hidden="true"
        >
          ST
        </div>
        <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-2">{title}</h1>
        {children}
      </div>
    </main>
  );
}
