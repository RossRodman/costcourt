import { Badge } from "@/components/ui";
import type { StreamStatus } from "@/features/debate/utils/debateState";

const STATUS: Record<StreamStatus, { label: string; tone: string; dot: string }> = {
  connecting: {
    label: "Connecting",
    tone: "text-ink-muted bg-surface-raised ring-line",
    dot: "bg-ink-faint animate-pulse",
  },
  running: {
    label: "Live",
    tone: "text-rose-200 bg-rose-400/10 ring-rose-400/30",
    dot: "bg-rose-400 animate-pulse",
  },
  completed: {
    label: "Ruled",
    tone: "text-emerald-200 bg-emerald-400/10 ring-emerald-400/25",
    dot: "bg-emerald-400",
  },
  failed: {
    label: "Failed",
    tone: "text-rose-200 bg-rose-400/10 ring-rose-400/25",
    dot: "bg-rose-400",
  },
};

interface StatusBadgeProps {
  status: StreamStatus;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const { label, tone, dot } = STATUS[status];
  return (
    <Badge tone={tone}>
      <span className={`size-1.5 rounded-full ${dot}`} aria-hidden />
      {label}
    </Badge>
  );
}
