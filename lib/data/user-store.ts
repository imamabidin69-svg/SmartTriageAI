import "server-only";
import { hashPassword } from "@/lib/password";
import type { Faskes, User } from "@/lib/schemas/triase.schema";

let faskesList: Faskes[] = [];
let users: User[] = [];
let seeded = false;

const FASKES_1_ID = "c0000000-0000-4000-8000-000000000001";
const FASKES_2_ID = "c0000000-0000-4000-8000-000000000002";
const FASKES_PUSAT_ID = "c0000000-0000-4000-8000-000000000099";

function seedIfEmpty(): void {
  if (seeded) return;
  seeded = true;

  faskesList = [
    { id: FASKES_1_ID, nama: "Puskesmas Kecamatan Madiun Lor" },
    { id: FASKES_2_ID, nama: "RSUD Dolopo" },
    { id: FASKES_PUSAT_ID, nama: "Kantor Pusat / Sistem" },
  ];

  const now = new Date().toISOString();
  users = [
    {
      id: "d0000000-0000-4000-8000-000000000001",
      nama: "Siti Aminah",
      email: "admin1@smarttriage.demo",
      passwordHash: hashPassword("Admin12345"),
      role: "admin_faskes",
      faskesId: FASKES_1_ID,
      isActive: true,
      createdAt: now,
    },
    {
      id: "d0000000-0000-4000-8000-000000000002",
      nama: "Ns. Ratna Wijaya",
      email: "perawat1@smarttriage.demo",
      passwordHash: hashPassword("Perawat123"),
      role: "perawat",
      faskesId: FASKES_1_ID,
      isActive: true,
      createdAt: now,
    },
    {
      id: "d0000000-0000-4000-8000-000000000003",
      nama: "dr. Bagus Kurniawan",
      email: "dpj1@smarttriage.demo",
      passwordHash: hashPassword("Dokter1234"),
      role: "dokter_pj",
      faskesId: FASKES_1_ID,
      isActive: true,
      createdAt: now,
    },
    {
      id: "d0000000-0000-4000-8000-000000000004",
      nama: "Budi Santoso",
      email: "admin2@smarttriage.demo",
      passwordHash: hashPassword("Admin56789"),
      role: "admin_faskes",
      faskesId: FASKES_2_ID,
      isActive: true,
      createdAt: now,
    },
    {
      id: "d0000000-0000-4000-8000-000000000005",
      nama: "Rina Marlina",
      email: "pendaftaran1@smarttriage.demo",
      passwordHash: hashPassword("Daftar123"),
      role: "petugas_pendaftaran",
      faskesId: FASKES_1_ID,
      isActive: true,
      createdAt: now,
    },
    {
      id: "d0000000-0000-4000-8000-000000000006",
      nama: "Eko Prabowo",
      email: "superadmin@smarttriage.demo",
      passwordHash: hashPassword("SuperAdmin1"),
      role: "super_admin",
      faskesId: FASKES_PUSAT_ID,
      isActive: true,
      createdAt: now,
    },
    {
      id: "d0000000-0000-4000-8000-000000000007",
      nama: "Wulan Sari",
      email: "auditor@smarttriage.demo",
      passwordHash: hashPassword("Auditor123"),
      role: "auditor",
      faskesId: FASKES_PUSAT_ID,
      isActive: true,
      createdAt: now,
    },
    {
      id: "d0000000-0000-4000-8000-000000000008",
      nama: "dr. Hartono, M.Kes",
      email: "dinkes@smarttriage.demo",
      passwordHash: hashPassword("DinasKes1"),
      role: "dinas_kesehatan",
      faskesId: FASKES_PUSAT_ID,
      isActive: true,
      createdAt: now,
    },
  ];
}

export function findUserByEmail(email: string): User | null {
  seedIfEmpty();
  const normalized = email.trim().toLowerCase();
  return users.find((u) => u.email.toLowerCase() === normalized) ?? null;
}

export function listAllFaskes(): Faskes[] {
  seedIfEmpty();
  return faskesList;
}

export function listAllUsers(): User[] {
  seedIfEmpty();
  return users;
}

export function getUserById(id: string): User | null {
  seedIfEmpty();
  return users.find((u) => u.id === id) ?? null;
}

export function getFaskesById(id: string): Faskes | null {
  seedIfEmpty();
  return faskesList.find((f) => f.id === id) ?? null;
}

export function listStaffByFaskes(faskesId: string): User[] {
  seedIfEmpty();
  return users.filter((u) => u.faskesId === faskesId).sort((a, b) => a.nama.localeCompare(b.nama));
}

export function emailExists(email: string): boolean {
  seedIfEmpty();
  return findUserByEmail(email) !== null;
}

export function emailExistsExcluding(email: string, excludeUserId: string): boolean {
  seedIfEmpty();
  const found = findUserByEmail(email);
  return found !== null && found.id !== excludeUserId;
}

export function insertUser(user: User): void {
  seedIfEmpty();
  users.push(user);
}

export function setUserActive(id: string, faskesId: string, isActive: boolean): User | null {
  seedIfEmpty();
  const idx = users.findIndex((u) => u.id === id && u.faskesId === faskesId);
  if (idx === -1) return null;
  const existing = users[idx];
  if (!existing) return null;
  const updated: User = { ...existing, isActive };
  users[idx] = updated;
  return updated;
}

export function setUserPasswordHash(id: string, faskesId: string, passwordHash: string): User | null {
  seedIfEmpty();
  const idx = users.findIndex((u) => u.id === id && u.faskesId === faskesId);
  if (idx === -1) return null;
  const existing = users[idx];
  if (!existing) return null;
  const updated: User = { ...existing, passwordHash };
  users[idx] = updated;
  return updated;
}

export function updateOwnProfile(id: string, changes: { nama: string; passwordHash?: string }): User | null {
  seedIfEmpty();
  const idx = users.findIndex((u) => u.id === id);
  if (idx === -1) return null;
  const existing = users[idx];
  if (!existing) return null;
  const updated: User = {
    ...existing,
    nama: changes.nama,
    passwordHash: changes.passwordHash ?? existing.passwordHash,
  };
  users[idx] = updated;
  return updated;
}

export function updateStaffInfo(
  id: string,
  faskesId: string,
  changes: { nama: string; email: string; role: User["role"] },
): User | null {
  seedIfEmpty();
  const idx = users.findIndex((u) => u.id === id && u.faskesId === faskesId);
  if (idx === -1) return null;
  const existing = users[idx];
  if (!existing) return null;
  const updated: User = { ...existing, nama: changes.nama, email: changes.email, role: changes.role };
  users[idx] = updated;
  return updated;
}
