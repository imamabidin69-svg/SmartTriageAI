/** Logo SmartTriage AI dari ikon PWA (kotak putih berisi perisai), dipakai di header admin, halaman masuk, dan Eir. */
export function LogoAplikasi({ ukuran = 30 }: { ukuran?: number }) {
  return <img src="/ikon-192.png" alt="" width={ukuran} height={ukuran} className="shrink-0" />;
}
