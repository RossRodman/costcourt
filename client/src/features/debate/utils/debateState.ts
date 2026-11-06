import type { DebateEvent, DebateReport, Debater, LLMUsage, Turn, Verdict } from "@/types";

export type StreamStatus = "connecting" | "running" | "completed" | "failed";

export interface DebateState {
  status: StreamStatus;
  lastEventId: number;
  speakers: Debater[];
  totalRounds: number | null;
  round: number;
  turns: Turn[];
  thinking: { role: Debater; round: number } | null;
  judging: { disputed: string[] } | null;
  verdict: Verdict | null;
  report: DebateReport | null;
  usage: LLMUsage[];
  error: string | null;
}

export const initialDebateState: DebateState = {
  status: "connecting",
  lastEventId: -1,
  speakers: [],
  totalRounds: null,
  round: 0,
  turns: [],
  thinking: null,
  judging: null,
  verdict: null,
  report: null,
  usage: [],
  error: null,
};

export type DebateAction =
  | { kind: "event"; id: number; event: DebateEvent }
  | { kind: "connection_lost" }
  | { kind: "reset" };

export function applyEvent(state: DebateState, event: DebateEvent): DebateState {
  switch (event.type) {
    case "debate_started":
      return {
        ...state,
        status: "running",
        speakers: event.speakers,
        totalRounds: event.rounds,
      };
    case "round_started":
      return { ...state, round: event.round, totalRounds: event.total_rounds };
    case "turn_started":
      return { ...state, thinking: { role: event.role, round: event.round } };
    case "turn_completed":
      return {
        ...state,
        thinking: null,
        turns: [...state.turns, event.turn],
        usage: [...state.usage, event.usage],
      };
    case "judge_started":
      return { ...state, thinking: null, judging: { disputed: event.disputed_item_ids } };
    case "verdict_reached":
      return { ...state, verdict: event.verdict, usage: [...state.usage, event.usage] };
    case "debate_completed":
      return {
        ...state,
        status: "completed",
        judging: null,
        thinking: null,
        report: event.report,
        verdict: event.report.verdict,
        turns: event.report.turns,
        usage: event.report.usage,
      };
    case "debate_failed":
      return { ...state, status: "failed", thinking: null, judging: null, error: event.error };
  }
}

export function debateReducer(state: DebateState, action: DebateAction): DebateState {
  switch (action.kind) {
    case "reset":
      return initialDebateState;
    case "connection_lost":
      if (state.status === "completed" || state.status === "failed") return state;
      return { ...state, status: "failed", error: "Lost the connection to the server." };
    case "event":
      if (action.id <= state.lastEventId) return state;
      return { ...applyEvent(state, action.event), lastEventId: action.id };
  }
}

export function isFinished(state: DebateState): boolean {
  return state.status === "completed" || state.status === "failed";
}

export function turnsByRound(turns: Turn[]): Map<number, Turn[]> {
  const rounds = new Map<number, Turn[]>();

  for (const turn of turns) {
    rounds.set(turn.round, [...(rounds.get(turn.round) ?? []), turn]);
  }

  return rounds;
}
