/**
 * Penyimpanan sesi Eir di sessionStorage, supaya percakapan tidak hilang saat halaman dimuat ulang. Backend tidak
 * menyediakan GET transkrip untuk pasien, jadi riwayat chat disimpan di peramban sampai tab ditutup.
 */
import type { StatusSesiEir } from "@/api/tipe";

const KUNCI_TAUTAN = "eir-tautan";
const KUNCI_SESI = "eir-sesi";

export interface PesanEir {
  peran: "eir" | "pengisi";
  teks: string;
}

export interface SesiEirTersimpan {
  idSesi: string;
  tokenSesi: string;
  kedaluwarsa: string;
  pesan: PesanEir[];
  status: StatusSesiEir;
  bolehSelesai: boolean;
  jumlahJawaban: number;
}

/** Token tautan ada di fragmen alamat (#t=...), sehingga tidak ikut terkirim ke server atau tercatat di log. */
export function tokenDariFragmen(fragmen: string): string | undefined {
  const token = new URLSearchParams(fragmen.replace(/^#/, "")).get("t");
  return token?.trim() || undefined;
}

function baca(kunci: string): string | null {
  try {
    return sessionStorage.getItem(kunci);
  } catch {
    return null;
  }
}

function tulis(kunci: string, nilai: string | null) {
  try {
    if (nilai === null) sessionStorage.removeItem(kunci);
    else sessionStorage.setItem(kunci, nilai);
  } catch {
    // Mode privat atau penyimpanan diblokir: percakapan tetap jalan, hanya tidak bertahan saat dimuat ulang.
  }
}

export function bacaTautan(): string | undefined {
  return baca(KUNCI_TAUTAN) ?? undefined;
}

export function simpanTautan(token: string | null) {
  tulis(KUNCI_TAUTAN, token);
}

export function bacaSesi(sekarang: Date = new Date()): SesiEirTersimpan | undefined {
  const teks = baca(KUNCI_SESI);
  if (!teks) return undefined;
  try {
    const sesi = JSON.parse(teks) as SesiEirTersimpan;
    if (!sesi.idSesi || !sesi.tokenSesi || Date.parse(sesi.kedaluwarsa) <= sekarang.getTime()) return undefined;
    return sesi;
  } catch {
    return undefined;
  }
}

export function simpanSesi(sesi: SesiEirTersimpan | null) {
  tulis(KUNCI_SESI, sesi ? JSON.stringify(sesi) : null);
}
