import { CornerDownRight } from "lucide-react";

import { Badge } from "@/components/ui";
import { lineChanges } from "@/features/debate/utils/lineChanges";
import { FigureChanges } from "@/features/debate/components/figureChanges";
import { ROLES, STANCES } from "@/constants";
import type { Argument, Estimate } from "@/types";

interface ArgumentItemProps {
  argument: Argument;
  estimate: Estimate | null;
}

export function ArgumentItem({ argument, estimate }: ArgumentItemProps) {
  const item = estimate?.items.find((i) => i.id === argument.line_item_id);
  const stance = STANCES[argument.stance];

  return (
    <li className="space-y-1.5">
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone={stance.tone}>{stance.label}</Badge>
        {argument.line_item_id && (
          <span className="font-mono text-xs text-ink-faint">{argument.line_item_id}</span>
        )}

        {item && <span className="truncate text-xs text-ink-muted">{item.description}</span>}
        {argument.rebuts && (
          <span className="inline-flex items-center gap-1 text-xs text-ink-faint">
            <CornerDownRight className="size-3" aria-hidden />
            answering the {ROLES[argument.rebuts].title.toLowerCase()}
          </span>
        )}
      </div>

      <p className="font-medium text-pretty">{argument.claim}</p>
      <p className="text-sm text-pretty text-ink-muted">{argument.reasoning}</p>
      {item && estimate && (
        <FigureChanges
          changes={lineChanges(
            item,
            estimate.currency,
            argument.proposed_quantity,
            argument.proposed_unit_rate,
          )}
        />
      )}
    </li>
  );
}
