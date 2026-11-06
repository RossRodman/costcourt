import type { HealthState } from "@/hooks/useHealth";
import { cn } from "@/utils/cn";

const VARIANTS = {
  loading: { dot: "bg-ink-faint animate-pulse", label: "Connecting…" },
  online: { dot: "bg-advocate", label: "API online" },
  noKey: { dot: "bg-estimator", label: "API online · no Claude key" },
  offline: { dot: "bg-red-400", label: "API offline" },
} as const;

interface StatusPillProps {
  state: HealthState;
}

export function StatusPill({ state }: StatusPillProps) {
  const variant =
    state.kind === "online" && !state.health.llm_configured ? VARIANTS.noKey : VARIANTS[state.kind];

  return (
    <span
      role="status"
      className="inline-flex items-center gap-2 rounded-full border border-line bg-surface px-3 py-1 text-xs text-ink-muted"
    >
      <span className={cn("size-1.5 rounded-full", variant.dot)} aria-hidden />
      {variant.label}
      {state.kind === "online" && (
        <span className="font-mono text-ink-faint">v{state.health.version}</span>
      )}
    </span>
  );
}
