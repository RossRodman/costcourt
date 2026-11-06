import type { LineItem } from "@/types";
import { formatMoney, formatQuantity } from "@/utils/format";

export interface LineChange {
  label: string;
  from: string;
  to: string;
}

export function lineChanges(
  item: LineItem,
  currency: string,
  quantity: number | null | undefined,
  unitRate: number | null | undefined,
): LineChange[] {
  const changes: LineChange[] = [];

  if (quantity != null && quantity !== item.quantity) {
    changes.push({
      label: "Qty",
      from: formatQuantity(item.quantity, item.unit),
      to: formatQuantity(quantity, item.unit),
    });
  }

  if (unitRate != null && unitRate !== item.unit_rate) {
    changes.push({
      label: "Rate",
      from: formatMoney(item.unit_rate, currency),
      to: formatMoney(unitRate, currency),
    });
  }

  return changes;
}
