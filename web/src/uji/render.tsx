import { QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactElement } from "react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { buatQueryClient, ruteAplikasi } from "@/App";

/** Merender aplikasi lengkap pada alamat tertentu, dengan cache query yang baru untuk setiap tes. */
export function renderRute(alamat: string) {
  const router = createMemoryRouter(ruteAplikasi, { initialEntries: [alamat] });
  const klien = buatQueryClient();
  klien.setDefaultOptions({ queries: { retry: false, refetchOnWindowFocus: false }, mutations: { retry: false } });
  const user = userEvent.setup();
  const hasil = render(
    <QueryClientProvider client={klien}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
  return { ...hasil, router, klien, user };
}

export function renderDenganQuery(elemen: ReactElement) {
  const klien = buatQueryClient();
  klien.setDefaultOptions({ queries: { retry: false } });
  const user = userEvent.setup();
  return { ...render(<QueryClientProvider client={klien}>{elemen}</QueryClientProvider>), klien, user };
}
