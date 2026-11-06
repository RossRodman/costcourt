import type { ReactNode } from "react";

import { Card, CardHeader } from "@/components/ui";
import type { Estimate } from "@/types";
import { formatMoney, formatMoneyDelta, formatNumber, formatUnit } from "@/utils/format";
import { cn } from "@/utils/cn";

interface RevisedEstimateProps {
  original: Estimate;
  revised: Estimate;
}

export function RevisedEstimate({ original, revised }: RevisedEstimateProps) {
  const revisedById = new Map(revised.items.map((item) => [item.id, item]));
  const money = (value: number) => formatMoney(value, original.currency);

  const changedCount = original.items.filter((item) => {
    const next = revisedById.get(item.id);
    return !next || next.total !== item.total;
  }).length;

  const totals: [string, number, number][] = [
    ["Direct cost", original.totals.direct_cost, revised.totals.direct_cost],
    [
      "Markups and tax",
      original.totals.grand_total - original.totals.direct_cost,
      revised.totals.grand_total - revised.totals.direct_cost,
    ],
    ["Grand total", original.totals.grand_total, revised.totals.grand_total],
  ];

  return (
    <Card>
      <CardHeader
        title="Revised estimate"
        description={`${changedCount} of ${original.items.length} lines changed by the verdict.`}
      />
      <div className="overflow-x-auto p-5">
        <table className="w-full min-w-[680px] text-sm">
          <thead>
            <tr className="border-b border-line text-left text-xs text-ink-faint">
              <th className="py-2 pr-3 font-medium">Item</th>
              <th className="py-2 pr-3 font-medium">Description</th>
              <th className="py-2 pr-3 text-right font-medium">Qty</th>
              <th className="py-2 pr-3 text-right font-medium">Rate</th>
              <th className="py-2 pr-3 text-right font-medium">Was</th>
              <th className="py-2 pr-3 text-right font-medium">Now</th>
              <th className="py-2 text-right font-medium">Change</th>
            </tr>
          </thead>

          <tbody className="tabular-nums">
            {original.items.map((item) => {
              const next = revisedById.get(item.id);
              const delta = (next?.total ?? 0) - item.total;
              const changed = !next || delta !== 0;
              return (
                <tr
                  key={item.id}
                  className={cn(
                    "border-b border-line/60 last:border-0",
                    changed ? "bg-estimator/5" : "text-ink-muted",
                    !next && "line-through",
                  )}
                >
                  <td className="py-2 pr-3 font-mono text-xs text-ink-faint">{item.id}</td>
                  <td className="py-2 pr-3">{item.description}</td>
                  <td className="py-2 pr-3 text-right whitespace-nowrap">
                    <Changed from={item.quantity} to={next?.quantity}>
                      {formatNumber(next?.quantity ?? item.quantity)} {formatUnit(item.unit)}
                    </Changed>
                  </td>
                  <td className="py-2 pr-3 text-right">
                    <Changed from={item.unit_rate} to={next?.unit_rate}>
                      {money(next?.unit_rate ?? item.unit_rate)}
                    </Changed>
                  </td>
                  <td className="py-2 pr-3 text-right text-ink-faint">{money(item.total)}</td>
                  <td className="py-2 pr-3 text-right">{next ? money(next.total) : "removed"}</td>
                  <td
                    className={cn(
                      "py-2 text-right",
                      delta > 0 && "text-amber-300",
                      delta < 0 && "text-sky-300",
                    )}
                  >
                    {changed ? formatMoneyDelta(delta, original.currency) : "—"}
                  </td>
                </tr>
              );
            })}
          </tbody>

          <tfoot className="tabular-nums">
            {totals.map(([label, was, now]) => (
              <tr key={label} className="border-t border-line font-medium last:text-base">
                <td colSpan={4} className="py-2 pr-3 text-right text-ink-muted">
                  {label}
                </td>
                <td className="py-2 pr-3 text-right text-ink-faint">{money(was)}</td>
                <td className="py-2 pr-3 text-right">{money(now)}</td>
                <td
                  className={cn(
                    "py-2 text-right",
                    now > was && "text-amber-300",
                    now < was && "text-sky-300",
                  )}
                >
                  {formatMoneyDelta(now - was, original.currency)}
                </td>
              </tr>
            ))}
          </tfoot>
        </table>
      </div>
    </Card>
  );
}

function Changed({
  from,
  to,
  children,
}: {
  from: number;
  to: number | undefined;
  children: ReactNode;
}) {
  return (
    <span className={cn(to !== undefined && to !== from && "font-medium text-estimator")}>
      {children}
    </span>
  );
}
