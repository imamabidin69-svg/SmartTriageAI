# SmartTriage AI — Modul 5, 6 & 7 (Next.js App Router + RSC + Zustand + TanStack Query)

Kelanjutan dari proyek [SmartTriageAI](https://github.com/imamabidin69-svg/SmartTriageAI)
(Modul 1-4). Tiga modul praktikum berikutnya — **Modul 5 (Framework Modern UI)**,
**Modul 6 (Next.js App Router & RSC)**, dan **Modul 7 (State Management: Zustand +
TanStack Query)** — dikerjakan sebagai **satu proyek Next.js terintegrasi**, karena
Modul 6 mewajibkan Next.js (berbasis React) dan Modul 7 memakai hooks React
(`@tanstack/react-query`) — sehingga pilihan framework Modul 5 otomatis jatuh ke
**React 19**.

**Penyusun:** Imam Abidin (V3925008) — D3 Teknik Informatika Kab. Madiun, Sekolah Vokasi UNS

## Cakupan

Alur **Tenaga Medis** yang sama dengan proyek sebelumnya (Login, Dashboard Antrean,
Form Input Triase, Hasil & Penjelasan AI), kini dengan arsitektur full-stack:

| Halaman | Rute | Server/Client |
|---|---|---|
| Login (RBAC) | `/login` | Server Component + `LoginFormClient` |
| Dashboard Antrean Prioritas | `/dashboard` | Server Component (prefetch+streaming) + `AntreanListClient` |
| Form Input Triase | `/triase/baru` | Server Component wrapper + `TriaseFormClient` |
| Hasil & Penjelasan AI | `/triase/[id]` | Server Component (`generateMetadata` dinamis) + `HasilTriaseClient` |

**Backend sungguhan** (bukan lagi localStorage) via Route Handlers:
`/api/auth/login`, `/api/auth/logout`, `/api/triase` (GET/POST),
`/api/triase/[id]` (GET), `/api/triase/[id]/validasi` (PATCH) — data tersimpan
in-memory di server (`lib/data/triase-store.ts`), reset saat server di-restart.

Tiga dokumen Matriks terpisah ada di `docs/`:
- `Matriks_Pemetaan_SRS_vs_UIComponent_Modul5.docx`
- `Matriks_Alignment_SRS_vs_FrontEnd_Modul6.docx`
- `Matriks_Analisis_Pemisahan_State_Modul7.docx`

## Cara Menjalankan

```bash
npm install
npm run build   # next build — strict TypeScript check + kompilasi penuh
npm start       # next start -p 3000, lalu buka http://localhost:3000
```

Untuk pengembangan dengan hot-reload:
```bash
npm run dev
```

**Login simulasi:** pilih peran "Perawat" atau "Dokter Penanggung Jawab (DPJ)" di
`/login` — tidak ada username/password sungguhan (di luar cakupan tugas front-end).

## Struktur Proyek

```
smarttriage-nextjs/
├── middleware.ts                       # Proteksi rute /dashboard & /triase (Modul 6)
├── app/
│   ├── layout.tsx                      # Root Layout — Metadata API statis, next/font (self-hosted)
│   ├── fonts.ts                        # next/font/local (self-hosted, tidak fetch ke Google Fonts saat build)
│   ├── providers.tsx                   # QueryClientProvider ("use client" — satu-satunya alasan)
│   ├── page.tsx                        # Redirect "/" -> /login atau /dashboard
│   ├── login/page.tsx
│   ├── (protected)/                    # Route Group: layout bersama Dashboard + Triase
│   │   ├── layout.tsx                  # Nested Layout — sidebar tidak remount saat navigasi
│   │   ├── dashboard/
│   │   │   ├── page.tsx                # RSC: prefetch + <Suspense> untuk AntreanStatsServer
│   │   │   ├── loading.tsx
│   │   │   └── error.tsx
│   │   └── triase/
│   │       ├── baru/page.tsx
│   │       └── [id]/
│   │           ├── page.tsx            # generateMetadata() dinamis
│   │           └── loading.tsx
│   └── api/
│       ├── auth/{login,logout}/route.ts
│       └── triase/route.ts, [id]/route.ts, [id]/validasi/route.ts
├── lib/
│   ├── schemas/triase.schema.ts        # Skema Zod (dipakai klien & server)
│   ├── types/branded.ts                # Branded Types
│   ├── classify.ts                     # AI Classification Engine (server-only)
│   ├── data/{triase-store.ts,stats.ts} # In-memory store + statistik (server-only)
│   ├── session.ts, constants.ts        # Sesi cookie httpOnly
│   ├── store/useUIStore.ts             # Zustand — Client UI State (Modul 7)
│   ├── query-client.ts, query-keys.ts  # Setup TanStack Query
│   ├── api-client.ts                   # fetch untuk Client Component
│   └── server-api.ts, server-fetch.ts  # fetch untuk Server Component (lihat catatan arsitektur di bawah)
├── hooks/useTriaseQueries.ts           # useQuery/useMutation custom hooks
├── components/
│   ├── ui/{button,card,risk-badge}.tsx # CVA, Server-safe (tanpa "use client")
│   ├── auth/LoginFormClient.tsx
│   ├── dashboard/*Client.tsx, AntreanStatsServer.tsx
│   └── triase/{TriaseFormClient,HasilTriaseClient}.tsx
└── docs/                               # 3 dokumen Matriks (Modul 5, 6, 7)
```

## Catatan Arsitektur Penting

**Route Handler dan Server Component TIDAK berbagi module state secara terjamin.**
Selama pengembangan, ditemukan bug nyata: `generateMetadata()` yang mengimpor
langsung fungsi dari `lib/data/triase-store.ts` gagal melihat data yang baru saja
disimpan lewat `POST /api/triase` — walau keduanya berjalan dalam proses
`next start` yang sama. Ini karena Next.js mengompilasi Route Handler dan RSC
sebagai target bundling terpisah.

**Solusi:** `lib/server-fetch.ts` + `lib/server-api.ts` membuat Server Component
memanggil Route Handler lewat HTTP sungguhan juga (persis seperti Client Component
lewat `lib/api-client.ts`), menjadikan Route Handler satu-satunya sumber kebenaran.
Lihat komentar di kedua berkas tersebut serta bagian 3 pada
`docs/Matriks_Alignment_SRS_vs_FrontEnd_Modul6.docx` untuk detail lengkap.

## Keterbatasan

- Data in-memory di server — reset saat restart (bukan PostgreSQL sungguhan).
- Alur Admin Fasilitas Kesehatan belum diimplementasikan (fokus alur Tenaga Medis).
- Bagian (a) Modul 5 (demo perbandingan React/Vue/Svelte generik) tidak dikerjakan
  karena bukan bagian yang dinilai rubrik — hanya Tugas Praktikum Mandiri (b).
- React Compiler (auto-memoization eksperimental) belum diaktifkan di `next.config.ts`.

## Pembaruan: Autentikasi Sungguhan & Kelola Akun Staf

Menindaklanjuti feedback pengujian, beberapa perubahan besar ditambahkan:

### 1. Login email+password sungguhan (menggantikan "pilih role")
Password di-hash dengan `scrypt` (bawaan Node `crypto`, tanpa dependency
tambahan) — lihat `lib/password.ts`. Pesan error login SENGAJA generik
("Email atau password salah") baik untuk email tak terdaftar maupun
password salah, mencegah *user enumeration*.

### 2. Registrasi dibatasi ke Admin Faskes saja
Tidak ada endpoint registrasi publik/self-service sama sekali. Hanya sesi
Admin Faskes yang bisa memanggil `POST /api/admin/staff` (lihat
`app/(protected)/admin/staff/page.tsx` + `StaffManagementClient.tsx`).
`faskesId` staf baru **selalu** disalin dari sesi admin yang mendaftarkan
— satu admin tidak bisa mendaftarkan akun untuk faskes lain.

### 3. Role yang bisa didaftarkan dibatasi
Admin Faskes hanya bisa memberi role yang "Terikat 1 Faskes" (Perawat, DPJ,
Petugas Pendaftaran, Admin Faskes) — `super_admin`/`auditor`/
`dinas_kesehatan` di luar wewenangnya (lihat `FacilityBoundRoleSchema`).

### 4. Lupa Password (stub)
`/lupa-password` + `POST /api/auth/forgot-password` — TIDAK mengirim email
sungguhan (belum ada server email). Selalu mengembalikan pesan sukses
generik yang sama untuk email terdaftar maupun tidak.

### 5. Kredensial Demo

| Role | Email | Password | Faskes |
|---|---|---|---|
| Admin Faskes | admin1@smarttriage.demo | Admin12345 | Puskesmas Kecamatan Madiun Lor |
| Perawat | perawat1@smarttriage.demo | Perawat123 | Puskesmas Kecamatan Madiun Lor |
| DPJ | dpj1@smarttriage.demo | Dokter1234 | Puskesmas Kecamatan Madiun Lor |
| Admin Faskes | admin2@smarttriage.demo | Admin56789 | RSUD Dolopo (untuk uji isolasi antar-faskes) |

### 6. Perbaikan lain dari feedback pengujian
- **Dark mode**: `Card`, `Button` (varian outline/secondary/ghost), dan
  header kini punya pasangan warna `dark:` lengkap (sebelumnya `bg-white`
  hardcoded membuat teks tak terbaca).
- **Validasi tanda vital**: dari blokir keras menjadi peringatan lunak —
  `lib/vital-warnings.ts` menampilkan dialog konfirmasi, bukan menolak
  input (kasus gawat darurat ekstrem tetap bisa didokumentasikan).
- **RBAC Setujui/Koreksi**: kasus risk level KRITIS kini wajib DPJ (Perawat
  tak bisa menyetujui sendiri walau sepakat dengan AI). Ditambah aksi baru
  **"Ajukan Review Dokter"** (FR-08) untuk Perawat yang tidak sepakat pada
  kasus non-kritis.
- **Input Triase**: sekarang benar-benar dibatasi ke role Perawat saja
  (sebelumnya DPJ juga bisa mengakses, bertentangan dengan tabel aktor SRS)
  — ditegakkan di tiga lapis: nav (disembunyikan), halaman (guard + pesan),
  dan Route Handler (403).

## Keterbatasan (diperbarui)

- Registrasi faskes PERTAMA (dan admin pertamanya) tidak punya alur
  onboarding sendiri — dua faskes demo di-seed langsung di
  `lib/data/user-store.ts`, meniru skenario "faskes baru diprovisikan oleh
  vendor/Dinas Kesehatan saat onboarding awal", bukan self-service.
- Password ditampilkan (bukan disembunyikan) di form registrasi staf,
  supaya Admin bisa langsung menyampaikan ke staf bersangkutan — ini
  trade-off UX yang disengaja untuk prototipe, bukan untuk produksi
  sungguhan (sebaiknya diganti alur invite-by-email di masa depan).
- Role Petugas Pendaftaran belum punya dashboard/fungsi UI sendiri (baru
  bisa didaftarkan lewat Kelola Akun Staf, belum punya halaman kerja).

## Pembaruan Kedua: Perbaikan Dark Mode, Poli/Dokter Rujukan, & Fitur Admin

### 1. Dark mode kini konsisten di semua rute
**Akar masalah:** tombol "+ Input Triase Baru" memakai tag `<a>` HTML biasa
(bukan `<Link>` Next.js), sehingga tiap diklik memicu **reload halaman
penuh** yang menghapus seluruh state JavaScript — termasuk Zustand
`themeMode` yang sebelumnya hanya hidup di memori browser. Diperbaiki
dengan: (1) mengganti `<a>` → `<Link>` di seluruh navigasi internal, (2)
menambahkan middleware `persist` Zustand (localStorage) supaya tema
bertahan lintas reload/refresh, (3) halaman Login & Lupa Password kini
**satu tampilan tetap** (semua kelas `dark:` dihapus + komponen
`ForcePublicAppearance` membersihkan sisa kelas "dark" di `<html>`).

### 2. Rujukan Poli & Dokter di Hasil Triase
`lib/poli-assignment.ts` — fungsi rule-based (mirip `classify()`) yang
menentukan poli tujuan & dokter penanggung (nama, jenis umum/spesialis,
spesialisasi) berdasarkan kata kunci gejala + risk level. Kasus KRITIS
selalu ke IGD. Field baru: `poliTujuan`, `dokterRujukan` pada
`TriageResultSchema` — sengaja dinamai "dokterRujukan" (bukan
"dokterPenanggungJawab") supaya tidak rancu dengan role RBAC "dokter_pj"
(DPJ) yang konsepnya berbeda (DPJ memvalidasi hasil AI, dokterRujukan
menangani pasien di poli).

### 3. Fitur baru Admin Faskes
- **Notifikasi permintaan reset password**: "Lupa Password" (sebelumnya
  stub murni) kini benar-benar membuat entri di antrean
  (`lib/data/password-reset-store.ts`) yang HANYA terlihat oleh Admin
  Faskes tempat staf tersebut terdaftar. Badge lonceng di header
  menampilkan jumlah pending (polling 30 detik), panel di `/admin/staff`
  menampilkan daftar + form "Reset Password" (Admin set password baru
  secara manual, tidak ada email sungguhan terkirim).
- **Search bar** staf: filter client-side by nama/email di halaman Kelola
  Akun Staf.
- **Profil Saya** (`/profil`, `PATCH /api/auth/profile`): tersedia untuk
  **semua role** (bukan cuma Admin) — ubah nama & password akun sendiri.
  Mengganti password wajib membuktikan tahu password lama walau sudah
  dalam sesi terautentikasi (pertahanan berlapis). Cookie sesi otomatis
  disinkronkan ulang jika nama berubah.

### Kredensial demo (password sudah diperbarui hasil pengujian, tapi seed asli tetap ini saat server baru dijalankan)

| Role | Email | Password |
|---|---|---|
| Admin Faskes | admin1@smarttriage.demo | Admin12345 |
| Perawat | perawat1@smarttriage.demo | Perawat123 |
| DPJ | dpj1@smarttriage.demo | Dokter1234 |
| Admin Faskes (faskes lain) | admin2@smarttriage.demo | Admin56789 |

## Pembaruan Ketiga: Diferensiasi Dashboard, UI Lengkap 7 Aktor SRS, & Pembersihan Copy

### 1. Dashboard Perawat vs DPJ kini berbeda
DPJ melihat judul "Antrean Validasi Klinis" + panel **"Perlu Tindakan Anda"**
yang menyaring kasus kritis belum divalidasi dan kasus yang diajukan Perawat
untuk ditinjau ulang — supaya DPJ langsung tahu apa yang butuh keputusannya,
bukan menyisir seluruh antrean. Perawat tetap melihat dashboard umum +
tombol "Input Triase Baru".

### 2. UI lengkap untuk seluruh 7 aktor SRS
Sebelumnya hanya Perawat, DPJ, dan Admin Faskes yang punya halaman kerja.
Kini seluruh aktor pada tabel SRS punya UI (beberapa fungsional penuh,
sebagian ringan/statis sesuai instruksi):

| Aktor | Halaman Baru | Status |
|---|---|---|
| Petugas Pendaftaran | `/pasien` — Registrasi Pasien | Fungsional penuh |
| Perawat | `/riwayat-pasien` — Riwayat Triase Pasien | Fungsional penuh |
| Perawat | `/asesmen-visual` — Asesmen Pasien Tidak Sadar | Fungsional penuh |
| Admin Faskes | `/admin/laporan` — Laporan & Statistik | Fungsional (agregat data nyata) |
| Super Admin | `/superadmin` — Kelola Faskes (lintas-faskes) | Fungsional (data nyata) |
| Super Admin | `/superadmin/konfigurasi-ai` — Konfigurasi Model AI | UI statis (state lokal, tidak persisten — di luar cakupan front-end) |
| Auditor | `/auditor` — Log Audit (lintas-faskes) | Fungsional penuh |
| Dinas Kesehatan | `/dinas-kesehatan` — Laporan Regional (lintas-faskes) | Fungsional penuh |

### 3. Perbaikan arsitektur data penting: isolasi antar-faskes
Ditemukan celah nyata: data triase sebelumnya **tidak dibatasi per faskes**
— dua faskes aktif akan saling melihat data pasien satu sama lain.
`TriageRecord` kini punya `faskesId`, dan `GET /api/triase` hanya
mengembalikan data milik faskes pengguna yang login. Diverifikasi dengan 2
faskes demo berbeda: RSUD Dolopo tidak melihat data Puskesmas Kecamatan
Madiun Lor sama sekali.

### 4. Log Audit lintas-faskes
`lib/data/audit-store.ts` — setiap aksi Setujui/Koreksi/Ajukan Review kini
tercatat sebagai entri audit tersendiri (siapa, kapan, risk level
sebelum/sesudah, catatan), terpisah dari record triase itu sendiri. Dipakai
oleh peran Auditor.

### 5. Registrasi Pasien terpisah dari Input Triase
Entitas `Pasien` baru (identitas: nama, NIK, tanggal lahir, alamat, no.
telepon) — didaftarkan Petugas Pendaftaran (jalur normal) atau Perawat
(jalur darurat, pasien tidak sadar tanpa pendamping) sebelum triase klinis
dilakukan.

### 6. Pembersihan copy UI
Seluruh teks yang terkesan "demo"/dokumentasi teknis (kredensial demo di
halaman login, catatan "prototipe", kode `(FR-xx)`/`(NFR-xx)` yang bocor ke
pesan pengguna) sudah dihapus dari antarmuka — tetap ada di komentar kode
untuk keperluan dokumentasi teknis, tapi tidak lagi terlihat pengguna akhir.

### Kredensial Demo Lengkap (8 akun, 3 faskes)

| Role | Email | Password | Faskes |
|---|---|---|---|
| Admin Faskes | admin1@smarttriage.demo | Admin12345 | Puskesmas Kecamatan Madiun Lor |
| Perawat | perawat1@smarttriage.demo | Perawat123 | Puskesmas Kecamatan Madiun Lor |
| DPJ | dpj1@smarttriage.demo | Dokter1234 | Puskesmas Kecamatan Madiun Lor |
| Petugas Pendaftaran | pendaftaran1@smarttriage.demo | Daftar123 | Puskesmas Kecamatan Madiun Lor |
| Admin Faskes | admin2@smarttriage.demo | Admin56789 | RSUD Dolopo |
| Super Admin | superadmin@smarttriage.demo | SuperAdmin1 | Kantor Pusat / Sistem (lintas-faskes) |
| Auditor | auditor@smarttriage.demo | Auditor123 | Kantor Pusat / Sistem (lintas-faskes) |
| Dinas Kesehatan | dinkes@smarttriage.demo | DinasKes1 | Kantor Pusat / Sistem (lintas-faskes, eksternal) |

### Keterbatasan Baru

- Konfigurasi Model AI (Super Admin) murni UI — perubahan tidak memengaruhi
  `lib/classify.ts` yang sesungguhnya dan tidak persisten (reset saat reload).
- Asesmen Pasien Tidak Sadar tetap memakai pipeline `classify()` yang sama;
  observasi checklist dirangkai otomatis jadi teks gejala, bukan model
  computer vision sungguhan.
- Registrasi Pasien dan Input Triase masih dua entitas terpisah yang belum
  saling terhubung erat (Perawat mengisi nama pasien bebas di form triase,
  belum memilih dari daftar Pasien terdaftar) — peningkatan lanjutan di
  luar cakupan saat ini.

## Pembaruan Keempat: Edit Akun Staf & Palet Warna Lebih Nyaman

### 1. Admin Faskes kini bisa mengedit akun nakes lain
Tombol "Edit" baru di tabel Kelola Akun Staf membuka form inline (nama,
email, peran) untuk staf SELAIN akun sendiri. `PATCH /api/admin/staff/[id]`
kini menangani dua jenis aksi sekaligus berdasarkan bentuk body:
`{isActive}` untuk toggle (fitur lama), atau `{nama, email, role}` untuk
edit info (fitur baru) — email diverifikasi unik (kecuali milik akun itu
sendiri), role dibatasi ke `FacilityBoundRoleSchema` yang sama seperti
saat registrasi, dan admin tidak bisa mengedit akunnya sendiri lewat jalur
ini (dialihkan ke `/profil`).

### 2. Palet warna dilunakkan (light & dark mode)
Sumber utama kesan "ngejreng": `RiskBadge` (Rendah/Sedang/Tinggi/KRITIS)
sebelumnya **tidak punya varian dark mode sama sekali** — badge pastel
terang selalu tampil solid di atas card gelap. Diperbaiki, plus beberapa
penyesuaian lapisan warna:
- Halaman (dark): `slate-950` (nyaris hitam) → `slate-900`
- Card/panel (dark): `slate-900` → `slate-800` (elevasi lebih jelas dari halaman)
- Input di dalam form (dark): dibuat sedikit "menjorok" (`slate-900`) — beda dari panel form (`slate-800`)
- Header: `slate-900` → `slate-800`
- Tombol primer/destruktif: ditambah varian `dark:` (lebih redup dari sebelumnya, yang memakai warna sama persis di kedua mode)
- Teks utama dark mode: `slate-100` (putih pekat) → `slate-200` (lebih lembut)

## Pembaruan Kelima: 6 Fitur Lanjutan

### 1. Notifikasi kasus kritis real-time (menutup celah FR-13)
`KritisNotificationWatcher` dipasang di layout terproteksi — polling
15 detik, toast otomatis muncul HANYA untuk kasus kritis yang benar-benar
baru (bukan yang sudah ada sejak awal sesi), plus badge 🚨 persisten di
header untuk DPJ.

### 2. Pasien tersambung ke Form Input Triase
Form Input Triase kini punya pencarian pasien terdaftar (bukan input nama
bebas) — memilih pasien otomatis memakai `id` aslinya sebagai `idPasien`,
sehingga Riwayat Triase benar-benar terhubung lintas kunjungan. Fallback
"Pasien belum terdaftar" tetap tersedia untuk kasus darurat.

### 3. Konfigurasi Model AI benar-benar memengaruhi klasifikasi
`lib/data/ai-config-store.ts` menyimpan ambang batas skor (kritis/tinggi/
sedang); `classify()` membacanya secara langsung. Diverifikasi: gejala
identik menghasilkan risk level BERBEDA sebelum vs sesudah Super Admin
mengubah ambang batas.

### 4. Ekspor CSV & Cetak/Simpan PDF
`components/ui/export-buttons.tsx` — tombol "Unduh CSV" (format RFC 4180,
BOM UTF-8 untuk Excel) dan "Cetak / Simpan PDF" (`window.print()` bawaan
browser, sengaja melepas mode gelap sesaat sebelum mencetak supaya hasil
PDF tidak berlatar hitam). Tersedia di Laporan & Statistik (Admin Faskes)
dan Laporan Regional (Dinas Kesehatan).

### 5. Log Audit diperluas
Sebelumnya hanya mencatat Setujui/Koreksi/Ajukan Review triase. Sekarang
juga mencatat: staf didaftarkan/diedit/diaktifkan/dinonaktifkan, dan
pasien didaftarkan — Auditor bisa melihat jejak aktivitas menyeluruh,
bukan cuma validasi triase.

### 6. Search nama pasien di Dashboard Antrean
Filter gabungan: risk level (Zustand) + pencarian nama (state lokal),
bekerja bersamaan tanpa fetch ulang ke server.

## Pembaruan Keenam: Proyek Akhir Capstone (14 Bab)

Lanjutan dari brief Proyek Akhir 14 Bab. Bagian ini mendokumentasikan bab-bab
yang belum tercakup pembaruan sebelumnya.

### Bab i) Build Tools & Biome
Biome dipasang LANGSUNG ke proyek Next.js ini (`biome.json`, `npm run
biome:check` / `biome:fix`) — bukan cuma di proyek Vite terpisah. 120 isu
awal (mayoritas format/urutan import) sudah diberesi; 15 isu aksesibilitas
& correctness nyata diperbaiki manual satu-satu (bukan `--unsafe` membabi
buta), termasuk memperbaiki desain timer toast notifikasi yang berisiko
memakai closure basi. Status akhir: **0 error, 0 warning** di 98 file.

Next.js sendiri sudah memakai Turbopack (mesin Rust yang sama persis
dibahas Modul 8) sebagai bundler — jadi kombinasi proyek ini
(Turbopack+Biome) dan proyek Vite terpisah (Rolldown+Biome) sama-sama jadi
bukti kompetensi toolchain Rust/Go, hanya beda konteks pemakaian.

### Bab j) Core Web Vitals
Arsitektur RSC (Modul 6) sudah secara alami mendukung LCP/INP yang baik —
sebagian besar halaman adalah HTML hasil render server dengan JS klien
minimal, tanpa gambar besar yang perlu dioptimasi (aplikasi ini murni
form/data, tidak ada `<img>` sama sekali). `next/font` (self-hosted)
mencegah CLS akibat pergantian font. Skeleton loading (`loading.tsx`)
dimensinya disesuaikan dengan konten asli untuk menghindari reflow.

**Pengukuran field data sungguhan**: `@vercel/speed-insights` dan
`@vercel/analytics` sudah terpasang di `app/layout.tsx` — begitu di-deploy
ke Vercel, data LCP/INP/CLS pengunjung NYATA (bukan simulasi) otomatis
terkumpul dan terlihat di dashboard Vercel > Speed Insights. Ini penting:
skor Lighthouse lokal itu simulasi, sedangkan field data CrUX (yang
disebut di brief) baru bisa didapat SETELAH ada trafik sungguhan pasca
deploy.

### Bab k) Keamanan Sisi Klien
- **Cookie sesi ditandatangani (HMAC-SHA256)** — sebelumnya cookie sesi
  cuma `JSON.stringify()` polos, bisa diedit manual lewat DevTools untuk
  eskalasi privilese (ubah role jadi admin). Sekarang `lib/session-cookie.ts`
  menandatangani cookie dan MENOLAK payload apa pun yang tanda tangannya
  tidak cocok. Sudah diuji: cookie yang diedit manual otomatis dianggap
  tidak login.
- **Rate limiting login** — 5 percobaan gagal / 15 menit per kombinasi
  IP+email (`lib/rate-limit.ts`), mitigasi brute-force. Diuji: percobaan
  ke-6 beruntun langsung kena HTTP 429.
- **Security headers** (`next.config.ts`): `X-Frame-Options: DENY`
  (anti-clickjacking), `X-Content-Type-Options: nosniff`, `Referrer-Policy`,
  `Content-Security-Policy`. Catatan jujur: CSP masih menyertakan
  `unsafe-inline` pada script-src karena Next.js App Router menyuntikkan
  skrip bootstrap hidrasi inline — pengetatan penuh butuh setup nonce
  per-request yang di luar cakupan waktu pengerjaan saat ini.
- **Isolasi environment variable** — `SESSION_SECRET` (rahasia server,
  TIDAK ada prefiks `NEXT_PUBLIC_`) wajib diset di produksi (`.env.example`
  mendokumentasikan variabel yang dibutuhkan tanpa membocorkan nilai
  sungguhan).
- `sonar-project.properties` sudah disiapkan — lihat panduan verifikasi
  SonarCloud di bawah.

### Bab l) Integrasi API & Type-Safe Data Layer
Proyek ini memakai **RESTful API lewat Next.js Route Handler** sebagai
lapisan BFF (Backend for Frontend) — bukan tRPC/oRPC. Ini keputusan
sadar, bukan kekurangan: Route Handler Next.js YANG BERADA DI DALAM
proyek yang sama sudah secara arsitektur adalah pola BFF (front-end dan
lapisan API-nya satu deployment, satu repo). Type-safety end-to-end tetap
tercapai lewat cara lain yang setara secara prinsip dengan tRPC: skema Zod
yang SAMA (`lib/schemas/*.ts`) dipakai untuk validasi request DI SERVER
(Route Handler) maupun parsing response DI KLIEN (`lib/api-client.ts`) —
kalau bentuk data berubah di satu sisi, TypeScript langsung menandai error
di sisi lainnya, persis manfaat inti yang ditawarkan tRPC, tanpa
menambah dependency baru di proyek yang sudah besar ini.

### Bab m) DevOps, Deployment & CI/CD
`.github/workflows/ci.yml` — pipeline Quality Gate (Biome check → tsc
strict → build produksi → scan SonarCloud), jalan otomatis di setiap push
ke `main` dan setiap Pull Request. Deployment ke Vercel sendiri ditangani
integrasi native GitHub milik Vercel (bukan lewat GitHub Actions) — lihat
panduan langkah-demi-langkah di bawah.

---

## Panduan Deployment & Verifikasi (WAJIB dilakukan manual oleh mahasiswa)

Tiga langkah ini butuh akun Anda sendiri (GitHub, Vercel, SonarCloud) —
tidak bisa disiapkan otomatis dari sini. Urutan di bawah SENGAJA berurutan
karena Vercel dan SonarCloud sama-sama perlu menyambung ke repo GitHub
lebih dulu.

### 1. Push ke GitHub
```bash
# Dari folder proyek ini (sudah di-git init, commit awal sudah ada):
git remote add origin https://github.com/imamabidin69-svg/SmartTriageAI.git
git branch -M main
git push -u origin main
```
Kalau repo `SmartTriageAI` di GitHub Anda sudah berisi commit lain
(riwayat modul-modul sebelumnya), `git push` biasa mungkin ditolak karena
riwayatnya beda cabang — gunakan `git push -u origin main --force` HANYA
jika Anda yakin ingin menimpa isi repo lama dengan kode final ini.

### 2. Sambungkan Vercel
1. Buka https://vercel.com, masuk pakai akun GitHub Anda.
2. "Add New… > Project", pilih repo `SmartTriageAI`.
3. Vercel otomatis mendeteksi ini proyek Next.js — biarkan pengaturan build default.
4. **Wajib**: sebelum/sesudah deploy pertama, buka Settings > Environment
   Variables, tambahkan `SESSION_SECRET` dengan nilai acak panjang
   (jalankan `openssl rand -hex 32` di terminal untuk membuatnya).
5. Deploy. Setiap `git push` ke `main` berikutnya otomatis men-deploy ulang.
6. Salin URL production (`https://smarttriage-ai-xxx.vercel.app` atau
   domain kustom) ke bagian atas README ini untuk dilampirkan ke laporan.

### 3. Verifikasi SonarCloud
1. Buka https://sonarcloud.io, masuk pakai akun GitHub, impor organisasi & repo `SmartTriageAI`.
2. Di pengaturan proyek SonarCloud, sesuaikan `sonar.projectKey` dan
   `sonar.organization` di `sonar-project.properties` kalau berbeda dari
   yang sudah ditulis di berkas ini.
3. Buat token analisis (My Account > Security > Generate Token).
4. Di GitHub repo Settings > Secrets and variables > Actions, tambahkan
   secret `SONAR_TOKEN` (isi token dari langkah 3) dan `SESSION_SECRET`
   (nilai sama seperti di Vercel, dipakai workflow CI untuk build).
5. Push apa pun ke `main` — workflow `.github/workflows/ci.yml` otomatis
   jalan dan mengirim hasil analisis ke SonarCloud.
6. Setelah selesai, screenshot halaman Quality Gate SonarCloud (harus
   PASSED) untuk dilampirkan ke laporan pengumpulan.
