/** Perekam suara untuk mode suara Eir (keputusan W5). Rekaman hanya ada di memori lalu dikirim ke server. */
import { useCallback, useEffect, useRef, useState } from "react";

// Urutan pilihan format: webm/ogg di Chrome, Edge, dan Firefox; mp4 (m4a) di Safari.
const FORMAT = [
  { mimeType: "audio/webm;codecs=opus", ekstensi: "webm" },
  { mimeType: "audio/webm", ekstensi: "webm" },
  { mimeType: "audio/ogg;codecs=opus", ekstensi: "ogg" },
  { mimeType: "audio/mp4", ekstensi: "m4a" },
];

export const DURASI_MAKS_DETIK = 60;

export function dukungRekaman(): boolean {
  return typeof window !== "undefined" && "MediaRecorder" in window && Boolean(navigator.mediaDevices?.getUserMedia);
}

export function pilihFormat(): { mimeType?: string; ekstensi: string } {
  const cocok = FORMAT.find((f) => MediaRecorder.isTypeSupported(f.mimeType));
  return cocok ?? { ekstensi: "webm" };
}

export function useRekaman(onSelesai: (rekaman: Blob, namaBerkas: string) => void) {
  const [merekam, setMerekam] = useState(false);
  const [galat, setGalat] = useState<string>();
  const perekam = useRef<MediaRecorder | null>(null);
  const batasWaktu = useRef<ReturnType<typeof setTimeout>>(undefined);
  const callback = useRef(onSelesai);
  callback.current = onSelesai;

  const berhenti = useCallback(() => {
    clearTimeout(batasWaktu.current);
    if (perekam.current?.state === "recording") perekam.current.stop();
  }, []);

  const mulai = useCallback(async () => {
    setGalat(undefined);
    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      setGalat("Mikrofon tidak dapat dipakai. Izinkan akses mikrofon atau ketik jawaban.");
      return;
    }
    const format = pilihFormat();
    const recorder = new MediaRecorder(stream, format.mimeType ? { mimeType: format.mimeType } : undefined);
    const potongan: Blob[] = [];
    recorder.ondataavailable = (event) => {
      if (event.data.size) potongan.push(event.data);
    };
    recorder.onstop = () => {
      for (const track of stream.getTracks()) track.stop();
      setMerekam(false);
      perekam.current = null;
      const rekaman = new Blob(potongan, { type: recorder.mimeType || format.mimeType || "audio/webm" });
      if (rekaman.size) callback.current(rekaman, `rekaman.${format.ekstensi}`);
    };
    perekam.current = recorder;
    recorder.start();
    setMerekam(true);
    batasWaktu.current = setTimeout(berhenti, DURASI_MAKS_DETIK * 1000);
  }, [berhenti]);

  // Rekaman dihentikan bila komponen ditutup di tengah merekam.
  useEffect(() => berhenti, [berhenti]);

  return { merekam, galat, mulai, berhenti };
}
