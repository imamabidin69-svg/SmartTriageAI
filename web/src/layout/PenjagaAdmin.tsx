import { Navigate, useLocation } from "react-router";
import { useSaya } from "@/api/admin";
import { pesanError } from "@/api/klien";
import { Alert } from "@/components/ui/alert";
import { Memuat } from "@/components/ui/memuat";
import { LayoutAdmin } from "./LayoutAdmin";

export const PESAN_BUKAN_ADMIN =
  "Akun perawat dan dokter memakai aplikasi SmartTriage AI di Android. Web ini khusus admin.";

/** Hanya admin yang masuk boleh membuka halaman admin; selain itu diarahkan ke halaman login. */
export function PenjagaAdmin() {
  const saya = useSaya();
  const lokasi = useLocation();

  if (saya.isPending) return <Memuat teks="Memeriksa sesi..." />;
  if (saya.isError) {
    return (
      <div className="mx-auto max-w-md p-8">
        <Alert jenis="galat" judul="Sesi tidak dapat diperiksa">
          {pesanError(saya.error)}
        </Alert>
      </div>
    );
  }
  if (!saya.data) return <Navigate to="/login" replace state={{ dari: lokasi.pathname }} />;
  if (saya.data.peran !== "admin") return <Navigate to="/login" replace state={{ pesan: PESAN_BUKAN_ADMIN }} />;
  return <LayoutAdmin pengguna={saya.data} />;
}
