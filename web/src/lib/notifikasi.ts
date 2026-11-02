/** Notifikasi singkat (toast) yang dipakai lintas halaman. State tampilan disimpan di Zustand (Tech Stack Tabel 1). */
import { create } from "zustand";

export interface Notifikasi {
  id: number;
  pesan: string;
  jenis: "sukses" | "galat";
}

interface StateNotifikasi {
  daftar: Notifikasi[];
  tampilkan: (pesan: string, jenis?: Notifikasi["jenis"]) => void;
  tutup: (id: number) => void;
}

let berikutnya = 1;

export const useNotifikasi = create<StateNotifikasi>((set) => ({
  daftar: [],
  tampilkan: (pesan, jenis = "sukses") =>
    set((state) => ({ daftar: [...state.daftar, { id: berikutnya++, pesan, jenis }] })),
  tutup: (id) => set((state) => ({ daftar: state.daftar.filter((n) => n.id !== id) })),
}));
