"use client";

import { useEffect } from "react";

export function ForcePublicAppearance() {
  useEffect(() => {
    document.documentElement.classList.remove("dark");
  }, []);
  return null;
}
