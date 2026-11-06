import type { EstimateTotals, Markups } from "@/types";
import { formatMoney, formatNumber } from "@/utils/format";
import { cn } from "@/utils/cn";

interface TotalsSummaryProps {
  totals: EstimateTotals;
  markups: Markups;
  currency: string;
  className?: string;
}

export function TotalsSummary({ totals, markups, currency, className }: TotalsSummaryProps) {
  const rows: [string, number, number | null][] = [
    ["Direct cost", totals.direct_cost, null],
    ["Overhead", totals.overhead, markups.overhead],
    ["Profit", totals.profit, markups.profit],
    ["Contingency", totals.contingency, markups.contingency],
    ["Tax", totals.tax, markups.tax],
  ];

  return (
    <dl className={cn("space-y-1 text-sm tabular-nums", className)}>
      {rows.map(([label, value, pct]) => (
        <div key={label} className="flex justify-between gap-4 text-ink-muted">
          <dt>
            {label}
            {pct !== null && <span className="ml-1 text-ink-faint">({formatNumber(pct)}%)</span>}
          </dt>
          <dd>{formatMoney(value, currency)}</dd>
        </div>
      ))}

      <div className="flex justify-between gap-4 border-t border-line pt-2 font-medium">
        <dt>Grand total</dt>
        <dd>{formatMoney(totals.grand_total, currency)}</dd>
      </div>
    </dl>
  );
}
