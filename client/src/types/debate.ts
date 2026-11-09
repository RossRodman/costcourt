import type { Estimate } from "@/types";

export type Role = "estimator" | "engineer" | "advocate" | "judge";
export type Debater = Exclude<Role, "judge">;
export type Stance = "support" | "increase" | "decrease" | "missing";
export type Decision = "accepted" | "adjusted" | "rejected";

export interface Argument {
  line_item_id: string | null;
  stance: Stance;
  claim: string;
  reasoning: string;
  proposed_quantity?: number | null;
  proposed_unit_rate?: number | null;
  rebuts?: Role | null;
}

export interface Turn {
  round: number;
  role: Debater;
  summary: string;
  arguments: Argument[];
}

export interface Ruling {
  line_item_id: string;
  decision: Decision;
  approved_quantity?: number | null;
  approved_unit_rate?: number | null;
  reasoning: string;
  sided_with: Role[];
}

export interface Verdict {
  summary: string;
  rulings: Ruling[];
  confidence: number;
  recommendations: string[];
}

export interface LLMUsage {
  role: Role;
  round: number | null;
  model: string;
  input_tokens: number;
  output_tokens: number;
  cache_read_tokens: number;
}

export interface CostImpact {
  original_total: number;
  revised_total: number;
  delta: number;
  delta_pct: number;
}

export interface DebateReport {
  id: string;
  created_at: string;
  estimate: Estimate;
  revised_estimate: Estimate;
  turns: Turn[];
  verdict: Verdict;
  models: Partial<Record<Role, string>>;
  usage: LLMUsage[];
  impact: CostImpact;
  rounds: number;
}

export type DebateStatus = "running" | "completed" | "failed";

export interface Debate {
  id: string;
  status: DebateStatus;
  created_at: string;
  estimate: Estimate | null;
  estimate_id: string;
  estimate_title: string;
  rounds: number;
  demo: boolean;
  events: number;
  error: string | null;
  report: DebateReport | null;
}

export interface DebateRequest {
  sample_id?: string;
  estimate?: Estimate;
  rounds?: number;
  demo?: boolean;
}

interface EventBase {
  at: string;
}

export type DebateEvent = EventBase &
  (
    | {
        type: "debate_started";
        debate_id: string;
        estimate_id: string;
        estimate_title: string;
        rounds: number;
        speakers: Debater[];
      }
    | { type: "round_started"; round: number; total_rounds: number }
    | { type: "turn_started"; round: number; role: Debater }
    | { type: "turn_completed"; turn: Turn; usage: LLMUsage }
    | { type: "judge_started"; disputed_item_ids: string[] }
    | { type: "verdict_reached"; verdict: Verdict; usage: LLMUsage }
    | { type: "debate_completed"; report: DebateReport }
    | { type: "debate_failed"; error: string }
  );

export type DebateEventType = DebateEvent["type"];

export const EVENT_TYPES: readonly DebateEventType[] = [
  "debate_started",
  "round_started",
  "turn_started",
  "turn_completed",
  "judge_started",
  "verdict_reached",
  "debate_completed",
  "debate_failed",
];
