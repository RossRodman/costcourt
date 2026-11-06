import { ThinkingCard } from "@/features/debate/components/thinkingCard";
import { TurnCard } from "@/features/debate/components/turnCard";
import { type DebateState, turnsByRound } from "@/features/debate/utils/debateState";
import type { Estimate } from "@/types";

interface TranscriptProps {
  state: DebateState;
  estimate: Estimate | null;
}

export function Transcript({ state, estimate }: TranscriptProps) {
  const rounds = turnsByRound(state.turns);

  if (state.thinking && !rounds.has(state.thinking.round)) {
    rounds.set(state.thinking.round, [])
  };

  if (state.round > 0 && !rounds.has(state.round)) {
    rounds.set(state.round, [])
  };

  return (
    <div className="space-y-10">
      {[...rounds.entries()].map(([round, turns]) => (
        <section key={round} aria-labelledby={`round-${round}`} className="space-y-4">
          <h2
            id={`round-${round}`}
            className="flex items-center gap-3 text-xs font-medium tracking-wide text-ink-faint uppercase"
          >
            Round {round}
            {state.totalRounds && <span className="font-normal">of {state.totalRounds}</span>}
            <span className="h-px flex-1 bg-line" />
          </h2>

          {turns.map((turn) => (
            <TurnCard key={`${turn.round}-${turn.role}`} turn={turn} estimate={estimate} />
          ))}

          {state.thinking?.round === round && <ThinkingCard role={state.thinking.role} />}
        </section>
      ))}
    </div>
  );
}
