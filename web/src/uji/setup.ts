import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterAll, afterEach, beforeAll } from "vitest";
import { aturCookie } from "./cookie";
import { server } from "./server";

// jsdom belum mendukung showModal/close pada <dialog>.
HTMLDialogElement.prototype.showModal = function showModal(this: HTMLDialogElement) {
  this.setAttribute("open", "");
};
HTMLDialogElement.prototype.close = function close(this: HTMLDialogElement) {
  this.removeAttribute("open");
};

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => {
  cleanup();
  server.resetHandlers();
  sessionStorage.clear();
  for (const nama of ["csrf_access_token", "csrf_refresh_token"]) {
    aturCookie(nama, "", "Thu, 01 Jan 1970 00:00:00 GMT");
  }
});
afterAll(() => server.close());
