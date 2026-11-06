import { TotalsSummary } from "@/components/totalsSummary";
import { Card, CardHeader } from "@/components/ui";
import { Participants } from "@/features/debate/components/participants";
import type { DebateState } from "@/features/debate/utils/debateState";
import type { Estimate } from "@/types";

interface DebateSidebarProps {
  state: DebateState;
  estimate: Estimate | null;
}

export function DebateSidebar({ state, estimate }: DebateSidebarProps) {
  return (
    <aside className="space-y-4 lg:sticky lg:top-6 lg:self-start">
      <Participants state={state} />
      {estimate && (
        <Card>
          <CardHeader
            title="Estimate under review"
            description={`${estimate.items.length} line items · ${estimate.currency}`}
          />
          <TotalsSummary
            totals={estimate.totals}
            markups={estimate.markups}
            currency={estimate.currency}
            className="p-5"
          />
        </Card>
      )}
    </aside>
  );
}
