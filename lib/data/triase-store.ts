import "server-only";
import type { TriageRecord } from "@/lib/schemas/triase.schema";

/**
 * In-memory data store (server-side only).
 * ---------------------------------------------------------------------------
 * Menggantikan localStorage dari proyek Modul 1-4. Modul 6 memperkenalkan
 * Route Handlers (route.ts) sebagai Web API sungguhan yang berjalan di
 * server — modul ini memanfaatkannya sebagai "backend" simulasi SmartTriage
 * AI, sehingga Modul 7 (TanStack Query) benar-benar melakukan fetch HTTP ke
 * endpoint nyata, bukan lagi membaca localStorage di klien.
 *
 * KETERBATASAN (didokumentasikan, bukan bug): data disimpan di memori proses
 * Node.js, sehingga akan RESET setiap kali server development di-restart
 * atau saat deploy baru terjadi. Pada implementasi produksi sungguhan, modul
 * ini digantikan oleh query ke PostgreSQL (lihat SKPL Bab V Arsitektur
 * Three-Tier).
 */

let records: TriageRecord[] = [];
let seeded = false;

function seedIfEmpty(): void {
  if (seeded) return;
  seeded = true;
  const now = Date.now();
  records = [
    {
      idPasien: "a1a1a1a1-0001-4000-8000-000000000001",
      idTriase: "b1b1b1b1-0001-4000-8000-000000000001",
      namaPasien: "Ahmad Fauzi",
      gejala: "Nyeri dada menjalar ke lengan kiri, sesak napas mendadak.",
      keluhanUtama: "Nyeri dada hebat",
      riwayatSingkat: "Riwayat hipertensi 5 tahun",
      tandaVital: {
        tekananDarahSistolik: 168,
        tekananDarahDiastolik: 102,
        suhuTubuh: 37.1,
        nadiPerMenit: 118,
        lajuNapas: 28,
        saturasiOksigen: 91,
      },
      riskLevel: "kritis",
      penjelasanAi:
        "Kombinasi nyeri dada khas, saturasi oksigen rendah (91%), dan takikardia (118 bpm) mengindikasikan kemungkinan sindrom koroner akut. Direkomendasikan penanganan segera.",
      statusValidasi: "menunggu",
      waktuTriase: new Date(now - 3 * 60_000).toISOString(),
      poliTujuan: "IGD (Instalasi Gawat Darurat)",
      dokterRujukan: { nama: "dr. Agus Prasetyo", jenis: "umum" },
      faskesId: "c0000000-0000-4000-8000-000000000001",
      dibuatOlehUserId: "d0000000-0000-4000-8000-000000000002",
      dibuatOlehNama: "Ns. Ratna Wijaya",
    },
    {
      idPasien: "a1a1a1a1-0002-4000-8000-000000000002",
      idTriase: "b1b1b1b1-0002-4000-8000-000000000002",
      namaPasien: "Dewi Lestari",
      gejala: "Demam 2 hari, batuk pilek, tidak ada sesak.",
      keluhanUtama: "Demam dan batuk",
      tandaVital: {
        tekananDarahSistolik: 112,
        tekananDarahDiastolik: 74,
        suhuTubuh: 38.2,
        nadiPerMenit: 92,
        lajuNapas: 20,
        saturasiOksigen: 98,
      },
      riskLevel: "sedang",
      penjelasanAi:
        "Demam ringan dengan tanda vital lain dalam batas normal. Kemungkinan infeksi saluran napas atas, dapat menunggu antrean sesuai giliran.",
      statusValidasi: "disetujui",
      waktuTriase: new Date(now - 20 * 60_000).toISOString(),
      poliTujuan: "Poli Paru",
      dokterRujukan: { nama: "dr. Yuni Kristiani, Sp.P", jenis: "spesialis", spesialisasi: "Paru" },
      faskesId: "c0000000-0000-4000-8000-000000000001",
      dibuatOlehUserId: "d0000000-0000-4000-8000-000000000002",
      dibuatOlehNama: "Ns. Ratna Wijaya",
      divalidasiOlehUserId: "d0000000-0000-4000-8000-000000000003",
      divalidasiOlehNama: "dr. Bagus Kurniawan",
    },
  ];
}

/** Dipakai halaman/Route Handler yang terikat 1 faskes (Dashboard, Riwayat, dll). */
export function listTriase(faskesId: string): TriageRecord[] {
  seedIfEmpty();
  const order: Record<TriageRecord["riskLevel"], number> = { kritis: 0, tinggi: 1, sedang: 2, rendah: 3 };
  return [...records].filter((r) => r.faskesId === faskesId).sort((a, b) => order[a.riskLevel] - order[b.riskLevel]);
}

/** Lintas-faskes - HANYA untuk role yang memang tidak terikat 1 faskes (Dinas Kesehatan, Super Admin). */
export function listTriaseAllFaskes(): TriageRecord[] {
  seedIfEmpty();
  return [...records];
}

export function getTriaseById(idTriase: string): TriageRecord | null {
  seedIfEmpty();
  return records.find((r) => r.idTriase === idTriase) ?? null;
}

export function insertTriase(record: TriageRecord): void {
  seedIfEmpty();
  records.unshift(record);
}

export function updateTriase(idTriase: string, updater: (existing: TriageRecord) => TriageRecord): TriageRecord | null {
  seedIfEmpty();
  const idx = records.findIndex((r) => r.idTriase === idTriase);
  if (idx === -1) return null;
  const existing = records[idx];
  if (!existing) return null;
  const updated = updater(existing);
  records[idx] = updated;
  return updated;
}
