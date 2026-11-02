/** jsdom belum mendukung Cookie Store API, jadi cookie tes diatur lewat document.cookie. */
export function aturCookie(nama: string, nilai: string, kedaluwarsa?: string) {
  const akhir = kedaluwarsa ? `; expires=${kedaluwarsa}` : "";
  // biome-ignore lint/suspicious/noDocumentCookie: hanya untuk tes, sama dengan cookie CSRF dari Flask-JWT-Extended
  document.cookie = `${nama}=${nilai}; path=/${akhir}`;
}
