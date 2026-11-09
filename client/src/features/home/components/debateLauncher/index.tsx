import { ArrowRight, LoaderCircle, Play, Sparkles } from "lucide-react";

import { Alert, BaseButton, Card } from "@/components/ui";
import { cn } from "@/utils/cn";

const ROUND_OPTIONS = [1, 2, 3] as const;

interface DebateLauncherProps {
  rounds: number;
  canStart: boolean;
  canDemo: boolean;
  missingKey: boolean;
  pending: boolean;
  error: string | null;
  onStart: (demo: boolean) => void;
  onRoundsChange: (rounds: number) => void;
}

export function DebateLauncher({
  rounds,
  canStart,
  canDemo,
  missingKey,
  pending,
  error,
  onStart,
  onRoundsChange,
}: DebateLauncherProps) {
  return (
    <>
      <Card className="flex flex-col gap-5 p-5 sm:flex-row sm:items-center">
        <fieldset className="flex items-center gap-3">
          <legend className="sr-only">Rounds</legend>
          <span className="text-sm text-ink-muted">Rounds</span>

          <div className="flex rounded-xl border border-line p-1">
            {ROUND_OPTIONS.map((n) => (
              <label
                key={n}
                className={cn(
                  "cursor-pointer rounded-lg px-3 py-1 text-sm transition-colors has-focus-visible:outline-2 has-focus-visible:outline-judge",
                  rounds === n ? "bg-surface-raised text-ink" : "text-ink-muted hover:text-ink",
                )}
              >
                <input
                  type="radio"
                  name="rounds"
                  value={n}
                  checked={rounds === n}
                  onChange={() => onRoundsChange(n)}
                  className="sr-only"
                />
                {n}
              </label>
            ))}
          </div>
        </fieldset>

        <div className="flex flex-wrap gap-3 sm:ml-auto">
          {canDemo && (
            <BaseButton variant="secondary" onClick={() => onStart(true)} disabled={pending}>
              <Sparkles className="size-4" aria-hidden />
              Watch a demo
            </BaseButton>
          )}

          <BaseButton onClick={() => onStart(false)} disabled={!canStart || pending}>
            {pending ? (
              <LoaderCircle className="size-4 animate-spin" aria-hidden />
            ) : (
              <Play className="size-4" aria-hidden />
            )}
            Start debate
            <ArrowRight className="size-4" aria-hidden />
          </BaseButton>
        </div>
      </Card>

      {missingKey && (
        <Alert tone="info" title="Live debates need a Claude API key">
          Add <code className="font-mono">ANTHROPIC_API_KEY</code> to{" "}
          <code className="font-mono">backend/.env</code> to run real agents.
          {canDemo
            ? " Until then, “Watch a demo” replays a recorded debate on this sample."
            : " The warehouse sample has a recorded demo you can watch without a key."}
        </Alert>
      )}

      {error && <Alert title="Couldn't start the debate">{error}</Alert>}
    </>
  );
}
