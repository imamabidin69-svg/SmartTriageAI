import "server-only";
import type { Pasien } from "@/lib/schemas/pasien.schema";

let pasienList: Pasien[] = [];
let seeded = false;

function seedIfEmpty(): void {
  if (seeded) return;
  seeded = true;
  pasienList = [
    {
      id: "a1a1a1a1-0001-4000-8000-000000000001",
      nama: "Ahmad Fauzi",
      nik: "3319012345670001",
      tanggalLahir: "1985-04-12",
      jenisKelamin: "laki_laki",
      alamat: "Jl. Merdeka No. 12, Madiun",
      noTelepon: "081234567801",
      faskesId: "c0000000-0000-4000-8000-000000000001",
      didaftarkanOlehUserId: "d0000000-0000-4000-8000-000000000002",
      didaftarkanOlehNama: "Ns. Ratna Wijaya",
      waktuDaftar: new Date(Date.now() - 5 * 60_000).toISOString(),
    },
    {
      id: "a1a1a1a1-0002-4000-8000-000000000002",
      nama: "Dewi Lestari",
      nik: "3319012345670002",
      tanggalLahir: "1992-11-03",
      jenisKelamin: "perempuan",
      alamat: "Jl. Sudirman No. 45, Madiun",
      noTelepon: "081234567802",
      faskesId: "c0000000-0000-4000-8000-000000000001",
      didaftarkanOlehUserId: "d0000000-0000-4000-8000-000000000002",
      didaftarkanOlehNama: "Ns. Ratna Wijaya",
      waktuDaftar: new Date(Date.now() - 25 * 60_000).toISOString(),
    },
  ];
}

export function listPasienByFaskes(faskesId: string): Pasien[] {
  seedIfEmpty();
  return pasienList.filter((p) => p.faskesId === faskesId).sort((a, b) => b.waktuDaftar.localeCompare(a.waktuDaftar));
}

export function getPasienById(id: string): Pasien | null {
  seedIfEmpty();
  return pasienList.find((p) => p.id === id) ?? null;
}

export function insertPasien(pasien: Pasien): void {
  seedIfEmpty();
  pasienList.push(pasien);
}
