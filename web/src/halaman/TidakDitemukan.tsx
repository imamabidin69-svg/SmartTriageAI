import { Link } from "react-router";

export function HalamanTidakDitemukan() {
  return (
    <div className="mx-auto max-w-md px-4 py-24 text-center">
      <h1 className="text-xl font-bold text-teks">Halaman tidak ditemukan</h1>
      <p className="mt-2 text-sm text-teks-2">Alamat yang dibuka tidak ada. Periksa kembali alamatnya.</p>
      <Link to="/" className="mt-6 inline-block text-sm font-bold text-biru hover:underline">
        Kembali ke beranda admin
      </Link>
    </div>
  );
}
