import { EstimateTable } from "@/components/estimateTable";
import { Card, CardHeader } from "@/components/ui";
import type { Estimate } from "@/types";

interface EstimatePreviewProps {
  estimate: Estimate;
}

export function EstimatePreview({ estimate }: EstimatePreviewProps) {
  const details = [estimate.location, `${estimate.items.length} line items`, estimate.currency]
    .filter(Boolean)
    .join(" · ");

  return (
    <Card>
      <CardHeader title={estimate.title} description={details} />
      <p className="px-5 pt-3 text-sm text-pretty text-ink-muted">{estimate.scope}</p>
      <EstimateTable estimate={estimate} className="p-5" />
    </Card>
  );
}
