import { type ReactNode, useState } from "react";
import type { SesiEirDibuat } from "@/api/tipe";
import { Alert } from "@/components/ui/alert";
import { bacaSesi, bacaTautan, type SesiEirTersimpan, simpanSesi, simpanTautan, tokenDariFragmen } from "@/lib/sesiEir";
import { KerangkaEir } from "./KerangkaEir";
import { Percakapan } from "./Percakapan";
import { Persetujuan } from "./Persetujuan";

interface Awal {
  token?: string;
  sesi?: SesiEirTersimpan;
}

/** Membaca token dari kode QR (#t=...) sekali, lalu menghapusnya dari alamat supaya tidak ikut dibagikan. */
function siapkanAwal(): Awal {
  const tokenBaru = tokenDariFragmen(window.location.hash);
  if (tokenBaru) {
    // Kode QR baru selalu memulai sesi baru.
    simpanTautan(tokenBaru);
    simpanSesi(null);
    window.history.replaceState(null, "", window.location.pathname);
    return { token: tokenBaru };
  }
  return { token: bacaTautan(), sesi: bacaSesi() };
}

export function HalamanEir() {
  const [awal] = useState(siapkanAwal);
  const [sesi, setSesi] = useState<SesiEirTersimpan | undefined>(awal.sesi);

  function ubah(baru: SesiEirTersimpan) {
    simpanSesi(baru);
    setSesi(baru);
  }

  function mulai(dibuat: SesiEirDibuat) {
    simpanTautan(null);
    ubah({
      idSesi: dibuat.id_sesi,
      tokenSesi: dibuat.token_sesi,
      kedaluwarsa: dibuat.kedaluwarsa,
      pesan: [{ peran: "eir", teks: dibuat.pesan }],
      status: "berjalan",
      bolehSelesai: false,
      jumlahJawaban: 0,
    });
  }

  let isi: ReactNode;
  if (sesi) isi = <Percakapan sesi={sesi} onUbah={ubah} />;
  else if (awal.token) isi = <Persetujuan token={awal.token} onMulai={mulai} />;
  else
    isi = (
      <Alert jenis="info" judul="Tautan Eir tidak lengkap">
        Buka Eir dengan memindai kode QR dari perawat. Bila kode QR sudah lebih dari dua jam, minta kode baru ke
        perawat.
      </Alert>
    );

  return <KerangkaEir>{isi}</KerangkaEir>;
}
