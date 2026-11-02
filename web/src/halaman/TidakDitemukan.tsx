import { Link } from "react-router";

export function HalamanTidakDitemukan() {
  return (
    <div className="mx-auto max-w-md px-4 py-24 text-center">
      <h1 className="text-xl font-semibold text-slate-900">Halaman tidak ditemukan</h1>
      <p className="mt-2 text-sm text-slate-600">Alamat yang dibuka tidak ada. Periksa kembali alamatnya.</p>
      <Link to="/" className="mt-6 inline-block text-sm font-medium text-blue-700 hover:underline">
        Kembali ke beranda admin
      </Link>
    </div>
  );
}
