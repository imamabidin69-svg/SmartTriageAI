/** Format angka dan waktu gaya Indonesia. Waktu dari server berupa UTC; rumah sakit memakai WIB. */

const ZONA_WIB = "Asia/Jakarta";

const formatWaktu = new Intl.DateTimeFormat("id-ID", {
  timeZone: ZONA_WIB,
  day: "numeric",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

const formatTanggal = new Intl.DateTimeFormat("id-ID", {
  timeZone: ZONA_WIB,
  day: "numeric",
  month: "short",
  year: "numeric",
});

export function waktuWib(iso: string): string {
  return `${formatWaktu.format(new Date(iso))} WIB`;
}

export function tanggal(iso: string): string {
  // Tanggal tanpa jam (YYYY-MM-DD) dibaca sebagai tengah hari WIB supaya tidak bergeser sehari.
  const nilai = /^\d{4}-\d{2}-\d{2}$/.test(iso) ? `${iso}T12:00:00+07:00` : iso;
  return formatTanggal.format(new Date(nilai));
}

/** Tanggal hari ini di WIB dalam format YYYY-MM-DD, digeser sejumlah hari. */
export function tanggalWib(geserHari = 0, dari: Date = new Date()): string {
  const waktu = new Date(dari.getTime() + geserHari * 86_400_000);
  const bagian = new Intl.DateTimeFormat("en-CA", { timeZone: ZONA_WIB }).format(waktu);
  return bagian;
}

export function angka(nilai: number, desimal = 0): string {
  return nilai.toLocaleString("id-ID", { minimumFractionDigits: 0, maximumFractionDigits: desimal });
}

export function persen(nilai: number | null | undefined): string {
  return nilai === null || nilai === undefined ? "-" : `${angka(nilai, 1)}%`;
}

export function selisihHari(dari: string, sampai: string): number {
  return Math.round((Date.parse(sampai) - Date.parse(dari)) / 86_400_000);
}
