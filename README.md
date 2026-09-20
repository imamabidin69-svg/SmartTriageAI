# SmartTriage AI

Sistem bantu triase pasien untuk IGD dan Puskesmas. Perawat mencatat gejala dan tanda vital, sistem memberi rekomendasi tingkat kegawatan beserta alasannya, dan Dokter Penanggung Jawab (DPJ) memvalidasi sebelum hasil itu dipakai — khusus kasus kritis, validasi DPJ wajib, tidak bisa disetujui sendiri oleh Perawat.

Proyek Tugas Akhir mata kuliah Pemrograman Web, D3 Teknik Informatika Kab. Madiun, Sekolah Vokasi UNS — Imam Abidin (V3925008).

**Live:** https://smart-triage-ai-eta.vercel.app
**Repo:** https://github.com/imamabidin69-svg/SmartTriageAI

## Peran Pengguna

Ada tujuh peran, masing-masing dengan halaman dan wewenang sendiri: Perawat menginput triase dan mendaftarkan pasien darurat; DPJ memvalidasi dan mengoreksi kasus kritis; Petugas Pendaftaran mengurus identitas pasien; Admin Faskes mengelola akun staf dan melihat laporan fasilitasnya; Super Admin mengatur seluruh faskes serta konfigurasi model AI; Auditor melihat log aktivitas lintas-faskes; dan Dinas Kesehatan mengakses laporan regional secara read-only. Wewenang tiap peran ditegakkan di server (Route Handler), bukan cuma disembunyikan di tampilan — jadi tidak bisa dilewati dengan memanggil API langsung.

## Menjalankan Secara Lokal

```bash
npm install
cp .env.example .env.local   # isi SESSION_SECRET dengan string acak
npm run dev                  # http://localhost:3000
```

Untuk build produksi: `npm run build && npm start`.

Login memakai email dan password sungguhan (di-hash dengan scrypt). Akun demo:

| Peran | Email | Password | Faskes |
|---|---|---|---|
| Admin Faskes | admin1@smarttriage.demo | Admin12345 | Puskesmas Kecamatan Madiun Lor |
| Perawat | perawat1@smarttriage.demo | Perawat123 | Puskesmas Kecamatan Madiun Lor |
| DPJ | dpj1@smarttriage.demo | Dokter1234 | Puskesmas Kecamatan Madiun Lor |
| Petugas Pendaftaran | pendaftaran1@smarttriage.demo | Daftar123 | Puskesmas Kecamatan Madiun Lor |
| Admin Faskes | admin2@smarttriage.demo | Admin56789 | RSUD Dolopo |
| Super Admin | superadmin@smarttriage.demo | SuperAdmin1 | Kantor Pusat |
| Auditor | auditor@smarttriage.demo | Auditor123 | Kantor Pusat |
| Dinas Kesehatan | dinkes@smarttriage.demo | DinasKes1 | Kantor Pusat |

Registrasi akun baru hanya bisa dilakukan Admin Faskes dari dalam sistem, tidak ada pendaftaran publik.

## Arsitektur

Dibangun dengan Next.js App Router — sebagian besar halaman adalah React Server Component yang mengambil data langsung di server, komponen klien dipakai seminimal mungkin hanya untuk bagian yang benar-benar interaktif (form, toggle, tombol aksi). State dipisah tegas: Zustand untuk preferensi tampilan (tema, filter yang dipilih), TanStack Query untuk data dari server (antrean, daftar staf, notifikasi), dengan cache invalidation otomatis tiap kali ada perubahan.

Komunikasi data lewat Route Handler (`app/api/**`) sebagai REST API, divalidasi Zod di kedua ujung — skema yang sama dipakai untuk memvalidasi request di server maupun memparse response di klien, jadi kalau bentuk data berubah di satu sisi, TypeScript langsung menandai galat di sisi lain. Satu hal yang perlu diperhatikan kalau mengembangkan lebih lanjut: Route Handler dan Server Component dikompilasi sebagai target terpisah oleh Next.js, jadi keduanya tidak otomatis berbagi state modul in-memory — `lib/server-api.ts` menyiasati ini dengan membuat Server Component memanggil Route Handler lewat HTTP juga, sama seperti komponen klien, supaya Route Handler tetap jadi satu-satunya sumber data yang benar.

Data triase, akun, dan pasien dipisah per faskes (`faskesId` di tiap record) — admin dan staf satu faskes tidak bisa melihat data faskes lain sama sekali. `tsconfig.json` memakai `strict` dan `noUncheckedIndexedAccess` penuh.

## Keamanan

Cookie sesi ditandatangani HMAC-SHA256 (`lib/session-cookie.ts`) supaya tidak bisa diubah manual lewat DevTools untuk eskalasi peran. Login dibatasi 5 percobaan gagal per 15 menit per kombinasi IP dan email. Header keamanan standar (X-Frame-Options, CSP, dll) diterapkan lewat `next.config.ts`. `SESSION_SECRET` dibaca dari environment variable server-side, tidak pernah ikut ter-bundle ke kode klien, dan aplikasi sengaja menolak start di produksi kalau variabel ini belum diset.

## Build Tools & Kualitas Kode

Linting dan formatting pakai Biome (`npm run biome:check`). Pipeline CI (`.github/workflows/ci.yml`) menjalankan Biome, type-check TypeScript, build produksi, dan scan SonarQube Cloud pada setiap push — semuanya lolos, termasuk Quality Gate SonarQube PASSED. Deployment ke Vercel otomatis lewat integrasi GitHub setiap push ke `main`.

Ada juga proyek Vite terpisah (`smarttriage-vite/`) yang membangun ulang alur inti sebagai SPA mandiri dengan Rolldown dan Biome, untuk keperluan praktikum build tools generasi baru.

## Struktur Proyek

```
app/
├── login/, lupa-password/              # Halaman publik
├── (protected)/                        # Wajib login — layout & sidebar bersama
│   ├── dashboard/, triase/             # Alur triase inti
│   ├── pasien/, riwayat-pasien/, asesmen-visual/
│   ├── admin/staff/, admin/laporan/    # Admin Faskes
│   ├── superadmin/, auditor/, dinas-kesehatan/
│   └── profil/
├── api/                                # Route Handler (REST + Zod)
└── proxy.ts                            # Route guard (dulu middleware.ts)

lib/
├── schemas/                            # Skema Zod — dipakai klien & server
├── data/                               # Store in-memory per domain
├── classify.ts, poli-assignment.ts     # Mesin rekomendasi AI
├── session.ts, session-cookie.ts, rate-limit.ts
└── api-client.ts, server-api.ts        # Lapisan fetch

components/, hooks/                     # Komponen & TanStack Query hooks per domain
docs/                                   # Dokumen matriks SRS per modul
```

## Keterbatasan

Data tersimpan in-memory di server, bukan database sungguhan — reset tiap server di-restart. Konfigurasi model AI (halaman Super Admin) memang benar-benar memengaruhi hasil klasifikasi, tapi asesmen pasien tidak sadar tetap memakai pipeline yang sama dengan input triase biasa, bukan model computer vision terpisah. Content-Security-Policy masih mengizinkan `unsafe-inline` untuk script karena Next.js menyuntikkan skrip hidrasi inline; pengetatan penuh butuh setup nonce per-request. Password staf baru ditampilkan langsung di form (bukan lewat email undangan) — sengaja begitu supaya Admin bisa langsung menyampaikan ke staf terkait.
