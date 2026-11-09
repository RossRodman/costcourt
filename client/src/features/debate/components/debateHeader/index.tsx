import { ArrowLeft, MapPin, Sparkles } from "lucide-react";
import { Link } from "react-router";

import { StatusBadge } from "@/components/statusBadge";
import { Badge } from "@/components/ui";
import type { DebateState } from "@/features/debate/utils/debateState";
import { Styled } from "@/styled";

interface DebateHeaderProps {
  title: string;
  location: string | null | undefined;
  demo: boolean;
  state: DebateState;
  back?: { to: string; label: string };
}

export function DebateHeader({
  title,
  location,
  demo,
  state,
  back = { to: "/", label: "New debate" },
}: DebateHeaderProps) {
  const progress =
    state.status !== "running" || !state.totalRounds
      ? null
      : state.judging || state.verdict
        ? "Judge's ruling"
        : `Round ${state.round || 1} of ${state.totalRounds}`;

  return (
    <header className="space-y-4">
      <Link
        to={back.to}
        className="inline-flex items-center gap-1.5 text-sm text-ink-muted hover:text-ink"
      >
        <ArrowLeft className="size-4" aria-hidden />
        {back.label}
      </Link>
      <div className="flex flex-wrap items-center gap-3">
        <StatusBadge status={state.status} />
        {demo && (
          <Badge tone="text-judge bg-judge/10 ring-judge/25">
            <Sparkles className="size-3" aria-hidden />
            Demo replay
          </Badge>
        )}
        {progress && <span className="text-sm text-ink-muted">{progress}</span>}
      </div>
      <h1 className={Styled.DetailTitle}>{title}</h1>
      {location && (
        <p className="flex items-center gap-1.5 text-sm text-ink-muted">
          <MapPin className="size-4" aria-hidden />
          {location}
        </p>
      )}
    </header>
  );
}
