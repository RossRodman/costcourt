import { ArrowRight } from "lucide-react";

import type { LineChange } from "@/features/debate/utils/lineChanges";

interface FigureChangesProps {
  changes: LineChange[];
}

export function FigureChanges({ changes }: FigureChangesProps) {
  if (changes.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2">
      {changes.map(({ label, from, to }) => (
        <span
          key={label}
          className="inline-flex items-center gap-1.5 rounded-lg bg-surface-raised px-2 py-1 font-mono text-xs tabular-nums"
        >
          <span className="text-ink-faint">{label}</span>
          <span className="text-ink-muted line-through decoration-ink-faint">{from}</span>
          <ArrowRight className="size-3 text-ink-faint" aria-label="to" />
          <span className="text-ink">{to}</span>
        </span>
      ))}
    </div>
  );
}
