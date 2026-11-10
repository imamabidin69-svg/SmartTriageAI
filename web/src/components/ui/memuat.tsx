export function Memuat({ teks = "Memuat data..." }: { teks?: string }) {
  return (
    <p role="status" className="py-8 text-center text-sm text-teks-3">
      {teks}
    </p>
  );
}
