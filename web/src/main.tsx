// Atkinson Hyperlegible Next (Braille Institute, SIL OFL): huruf dan angka dibuat mudah dibedakan.
// Berkas font ikut dibundel Vite, jadi tetap lolos CSP font-src 'self'.
import "@fontsource/atkinson-hyperlegible-next/latin-400.css";
import "@fontsource/atkinson-hyperlegible-next/latin-600.css";
import "@fontsource/atkinson-hyperlegible-next/latin-700.css";
import "./index.css";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";

const akar = document.getElementById("root");
if (akar) {
  createRoot(akar).render(
    <StrictMode>
      <App />
    </StrictMode>,
  );
}
