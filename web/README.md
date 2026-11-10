# Web SmartTriage AI (admin IGD dan Eir)

Aplikasi React untuk dua kelompok pengguna, sesuai SKPL v3.0 Tabel 7.2 dan 7.3:

- **Admin IGD**: Kelola Staf, Pengaturan Triase, Rekap (dengan ekspor CSV), Log Audit, dan ganti password.
  Perawat dan dokter memakai aplikasi Android, jadi akun mereka ditolak di web ini.
- **Pasien zona hijau atau keluarganya**: halaman Eir di `/eir`, dibuka dari kode QR yang dibuat perawat, tanpa akun.
  Jawaban bisa diketik atau direkam suara.

Hasil build disajikan Flask (SpaRoute) dari origin yang sama dengan API, lalu bisa dipasang sebagai PWA.

Tampilan mengikuti panduan gaya tahap 6D, sama dengan aplikasi mobile, dengan struktur mockup SKPL Gambar 7.2 dan
7.3 (header gelap berisi menu dan nama pengguna):

- Biru tua `#0F2A4F` diambil dari logo. Merah, oranye, kuning, dan hijau hanya dipakai untuk level risiko, dan hanya
  Kritis yang berlatar penuh. Token warnanya ada di `src/index.css`.
- Huruf Atkinson Hyperlegible Next (Braille Institute, lisensi SIL OFL) dari `@fontsource`, ikut dibundel Vite
  sehingga tetap lolos CSP `font-src 'self'`. Angka memakai angka rata (tabular).
- Logo dan ikon ada di `public/`: `favicon.ico`, `ikon-192.png`, `ikon-512.png`, `ikon-maskable-512.png`, dan
  `apple-touch-icon.png`. Komponen `LogoAplikasi` memakai `ikon-192.png`.

## Teknologi

React 19, TypeScript (strict), React Router 7, Tailwind CSS 4, TanStack Query 5, Zustand 5, Zod 3, Vite 7, dan
vite-plugin-pwa. Lint dan format memakai Biome; tes memakai Vitest, Testing Library, dan MSW. Semua versi dikunci di
`package.json` dan `package-lock.json`.

## Menjalankan

Backend harus sudah berjalan di `http://127.0.0.1:5000` (lihat `backend/README.md`).

```bash
cd web
npm ci
npm run dev        # http://localhost:5173, /api diteruskan ke Flask
```

Untuk mencoba hasil akhirnya lewat Flask:

```bash
npm run build      # menghasilkan web/dist
# lalu buka http://127.0.0.1:5000/staf
```

Untuk mencoba Eir tanpa kunci Groq, isi `LLM_EIR=tiruan` di `backend/.env`. Tautan Eir dibuat perawat lewat
`POST /api/v1/kunjungan/{id}/tautan-eir` (misalnya dari Swagger), lalu alamat `url` di responsnya dibuka di peramban.

## Pengujian dan lint

```bash
npm run lint          # Biome
npm run typecheck     # tsc --noEmit
npm run test:coverage # Vitest, batas coverage 80%
```

## Tipe dari OpenAPI

Bentuk data mengikuti model Pydantic backend. Bila skema backend berubah, ekspor ulang spesifikasinya lalu bangkitkan
tipe TypeScript:

```bash
cd ../backend && flask --app run openapi -o ../web/openapi.json -i 2
cd ../web && npm run api:tipe
```

## Struktur

```
src/
  api/          klien HTTP (cookie, CSRF, refresh token), hook TanStack Query, tipe dari OpenAPI
  components/ui tombol, kartu, isian, dialog, notifikasi, badge risk level
  halaman/      halaman admin, dan eir/ untuk halaman Eir
  layout/       kerangka admin dan penjaga akses
  lib/          format tanggal dan angka WIB, label, sesi Eir, perekam suara
  uji/          setup Vitest dan server MSW
```
