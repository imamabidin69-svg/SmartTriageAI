"use client";

import Link from "next/link";
import { Card } from "@/components/ui/card";
import { RiskBadge } from "@/components/ui/risk-badge";
import { useAntreanQuery } from "@/hooks/useTriaseQueries";

export function DpjPriorityQueueClient() {
  const { data } = useAntreanQuery();

  const perluTindakan =
    data?.filter(
      (r) =>
        (r.riskLevel === "kritis" && r.statusValidasi === "menunggu") || r.statusValidasi === "menunggu_review_dokter",
    ) ?? [];

  if (perluTindakan.length === 0) return null;

  return (
    <Card emphasis="critical" className="space-y-3">
      <h2 className="font-semibold text-red-800 dark:text-red-300">Perlu Tindakan Anda ({perluTindakan.length})</h2>
      <ul className="space-y-2">
        {perluTindakan.map((r) => (
          <li
            key={r.idTriase}
            className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-red-200 dark:border-red-900 p-3"
          >
            <div className="flex items-center gap-3">
              <RiskBadge level={r.riskLevel} />
              <div>
                <p className="text-sm font-medium text-slate-900 dark:text-slate-200">{r.namaPasien}</p>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {r.statusValidasi === "menunggu_review_dokter"
                    ? "Diajukan Perawat untuk ditinjau"
                    : "Menunggu validasi kasus kritis"}
                </p>
              </div>
            </div>
            <Link
              href={`/triase/${r.idTriase}`}
              className="text-sm font-medium text-blue-600 dark:text-blue-400 hover:underline"
            >
              Tinjau Sekarang →
            </Link>
          </li>
        ))}
      </ul>
    </Card>
  );
}
