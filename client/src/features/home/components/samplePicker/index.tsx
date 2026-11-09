import { CircleCheck, MapPin, Sparkles } from "lucide-react";

import { Badge, Skeleton } from "@/components/ui";
import type { EstimateSummary } from "@/types";
import { formatMoney } from "@/utils/format";
import { cn } from "@/utils/cn";

interface SamplePickerProps {
  samples: EstimateSummary[] | undefined;
  demos: string[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export function SamplePicker({ samples, demos, selectedId, onSelect }: SamplePickerProps) {
  if (!samples) {
    return (
      <div className="grid gap-3 md:grid-cols-3">
        {[0, 1, 2].map((i) => (
          <Skeleton key={i} className="h-32" />
        ))}
      </div>
    );
  }

  return (
    <div role="radiogroup" aria-label="Sample estimates" className="grid gap-3 md:grid-cols-3">
      {samples.map((sample) => {
        const selected = sample.id === selectedId;

        return (
          <button
            key={sample.id}
            type="button"
            role="radio"
            aria-checked={selected}
            onClick={() => onSelect(sample.id)}
            className={cn(
              "group relative flex flex-col gap-3 rounded-2xl border bg-surface p-4 text-left transition-colors",
              "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-judge",
              selected
                ? "border-judge/60 bg-judge/5"
                : "border-line hover:border-ink-faint hover:bg-surface-raised",
            )}
          >
            <div className="flex items-start justify-between gap-2">
              <span className="font-medium text-balance">{sample.title}</span>
              {selected ? (
                <CircleCheck className="size-5 shrink-0 text-judge" aria-hidden />
              ) : (
                <span className="size-5 shrink-0 rounded-full border border-line" aria-hidden />
              )}
            </div>

            {sample.location && (
              <span className="flex items-center gap-1 text-xs text-ink-muted">
                <MapPin className="size-3.5" aria-hidden />
                {sample.location}
              </span>
            )}

            <div className="mt-auto flex items-end justify-between gap-2">
              <span className="text-xs text-ink-faint">{sample.item_count} line items</span>
              <span className="font-mono text-sm tabular-nums">
                {formatMoney(sample.grand_total, sample.currency, { whole: true })}
              </span>
            </div>

            {demos.includes(sample.id) && (
              <Badge
                tone="text-judge bg-judge/10 ring-judge/25"
                className="absolute -top-2 right-3"
              >
                <Sparkles className="size-3" aria-hidden />
                Demo
              </Badge>
            )}
          </button>
        );
      })}
    </div>
  );
}
