import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createBrowserRouter, Navigate, RouterProvider } from "react-router";
import { ProblemError } from "@/api/klien";
import { HalamanEir } from "@/halaman/eir/HalamanEir";
import { HalamanGantiPassword } from "@/halaman/GantiPassword";
import { HalamanLogAudit } from "@/halaman/LogAudit";
import { HalamanLogin } from "@/halaman/Login";
import { HalamanPengaturan } from "@/halaman/Pengaturan";
import { HalamanRekap } from "@/halaman/Rekap";
import { HalamanStaf } from "@/halaman/Staf";
import { HalamanTidakDitemukan } from "@/halaman/TidakDitemukan";
import { PenjagaAdmin } from "@/layout/PenjagaAdmin";

export const ruteAplikasi = [
  { path: "/login", element: <HalamanLogin /> },
  // Halaman Eir untuk pasien atau keluarga, dibuka dari kode QR tanpa akun.
  { path: "/eir", element: <HalamanEir /> },
  {
    element: <PenjagaAdmin />,
    children: [
      { index: true, element: <Navigate to="/staf" replace /> },
      { path: "/staf", element: <HalamanStaf /> },
      { path: "/pengaturan", element: <HalamanPengaturan /> },
      { path: "/rekap", element: <HalamanRekap /> },
      { path: "/log-audit", element: <HalamanLogAudit /> },
      { path: "/akun/password", element: <HalamanGantiPassword /> },
    ],
  },
  { path: "*", element: <HalamanTidakDitemukan /> },
];

/** Error 4xx tidak diulang otomatis; hanya gangguan jaringan atau server yang dicoba ulang sekali. */
export function bolehUlang(jumlahGagal: number, galat: unknown): boolean {
  if (galat instanceof ProblemError && galat.status >= 400 && galat.status < 500) return false;
  return jumlahGagal < 1;
}

export function buatQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: bolehUlang, refetchOnWindowFocus: false },
      mutations: { retry: false },
    },
  });
}

const router = createBrowserRouter(ruteAplikasi);
const queryClient = buatQueryClient();

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
}
