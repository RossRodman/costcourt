import { TotalsSummary } from "@/components/totalsSummary";
import type { Estimate } from "@/types";
import { cn } from "@/utils/cn";
import { formatMoney, formatNumber, formatUnit } from "@/utils/format";

interface EstimateTableProps {
  estimate: Estimate;
  className?: string;
}

export function EstimateTable({ estimate, className }: EstimateTableProps) {
  const money = (value: number) => formatMoney(value, estimate.currency);

  return (
    <div className={cn("overflow-x-auto", className)}>
      <table className="w-full min-w-[640px] text-sm">
        <thead>
          <tr className="border-b border-line text-left text-xs text-ink-faint">
            <th className="py-2 pr-3 font-medium">Item</th>
            <th className="py-2 pr-3 font-medium">Description</th>
            <th className="py-2 pr-3 text-right font-medium">Qty</th>
            <th className="py-2 pr-3 font-medium">Unit</th>
            <th className="py-2 pr-3 text-right font-medium">Rate</th>
            <th className="py-2 text-right font-medium">Total</th>
          </tr>
        </thead>

        <tbody className="tabular-nums">
          {estimate.items.map((item) => (
            <tr key={item.id} className="border-b border-line/60 align-top last:border-0">
              <td className="py-2 pr-3 font-mono text-xs text-ink-faint">{item.id}</td>
              <td className="py-2 pr-3">
                {item.description}
                {item.notes && <p className="text-xs text-ink-faint">{item.notes}</p>}
              </td>
              <td className="py-2 pr-3 text-right">{formatNumber(item.quantity)}</td>
              <td className="py-2 pr-3 text-ink-muted">{formatUnit(item.unit)}</td>
              <td className="py-2 pr-3 text-right">{money(item.unit_rate)}</td>
              <td className="py-2 text-right">{money(item.total)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <TotalsSummary
        totals={estimate.totals}
        markups={estimate.markups}
        currency={estimate.currency}
        className="mt-4 ml-auto max-w-xs"
      />
    </div>
  );
}
