/** Panggilan API halaman Eir untuk pasien atau keluarga tanpa akun (FR-08, Desain 2.8). */
import { permintaan } from "./klien";
import type { BalasanEir, PengisiEir, SesiEirDibuat } from "./tipe";

function headerSesi(tokenSesi: string) {
  return { "X-Token-Eir": tokenSesi };
}

export function bukaSesi(token: string, pengisi: PengisiEir) {
  return permintaan<SesiEirDibuat>("/eir/sesi", { method: "POST", json: { token, setuju: true, pengisi } });
}

export function kirimPesan(idSesi: string, tokenSesi: string, teks: string) {
  return permintaan<BalasanEir>(`/eir/sesi/${idSesi}/pesan`, {
    method: "POST",
    json: { teks },
    header: headerSesi(tokenSesi),
    bolehRefresh: false,
  });
}

export function kirimSuara(idSesi: string, tokenSesi: string, rekaman: Blob, namaBerkas: string) {
  const form = new FormData();
  form.append("berkas", new File([rekaman], namaBerkas, { type: rekaman.type }));
  return permintaan<BalasanEir>(`/eir/sesi/${idSesi}/suara`, {
    method: "POST",
    form,
    header: headerSesi(tokenSesi),
    bolehRefresh: false,
  });
}

export function selesaikan(idSesi: string, tokenSesi: string) {
  return permintaan<BalasanEir>(`/eir/sesi/${idSesi}/selesai`, {
    method: "POST",
    header: headerSesi(tokenSesi),
    bolehRefresh: false,
  });
}
