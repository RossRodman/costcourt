import { Check } from "lucide-react";

import { Card, CardHeader, TypingDots } from "@/components/ui";
import { RoleAvatar } from "@/components/roleAvatar";
import { ROLE_ORDER, ROLES } from "@/constants";
import type { DebateState } from "@/features/debate/utils/debateState";
import type { Role } from "@/types";

type Activity = "waiting" | "thinking" | "done";

function activityOf(role: Role, state: DebateState): Activity {
  if (role === "judge") {
    if (state.verdict) return "done";
    return state.judging ? "thinking" : "waiting";
  }

  if (state.thinking?.role === role) return "thinking";

  return state.turns.some((t) => t.role === role) ? "done" : "waiting";
}

interface ParticipantsProps {
  state: DebateState;
}

export function Participants({ state }: ParticipantsProps) {
  return (
    <Card>
      <CardHeader title="The panel" />

      <ul className="space-y-1 p-3">
        {ROLE_ORDER.map((role) => {
          const activity = activityOf(role, state);
          const turns = state.turns.filter((t) => t.role === role).length;
          const model = state.report?.models[role];
          return (
            <li
              key={role}
              className="flex items-center gap-3 rounded-xl px-2 py-2 data-[active=true]:bg-surface-raised"
              data-active={activity === "thinking"}
            >
              <RoleAvatar role={role} size="sm" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm">{ROLES[role].title}</p>
                {model && <p className="truncate font-mono text-[11px] text-ink-faint">{model}</p>}
              </div>
              <span className="text-xs text-ink-faint">
                {activity === "thinking" && (
                  <span className="flex items-center gap-1.5 text-ink-muted">
                    <span className="sr-only">thinking</span>
                    <TypingDots />
                  </span>
                )}
                {activity === "done" &&
                  (role === "judge" ? (
                    <Check className="size-4 text-advocate" aria-label="ruled" />
                  ) : (
                    `${turns} ${turns === 1 ? "turn" : "turns"}`
                  ))}
                {activity === "waiting" && "waiting"}
              </span>
            </li>
          );
        })}
      </ul>
    </Card>
  );
}
