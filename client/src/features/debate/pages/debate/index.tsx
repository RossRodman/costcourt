import { Link, useParams } from "react-router";

import { ApiError } from "@/api";
import { Alert, Skeleton } from "@/components/ui";
import {
  DebateHeader,
  DebateSidebar,
  RevisedEstimate,
  ThinkingCard,
  Transcript,
  UsageDetails,
  VerdictPanel,
} from "@/features/debate/components";
import { useDebate, useDebateStream } from "@/features/debate/hooks";
import { NotFoundPage } from "@/features/notFound";

export function DebatePage() {
  const { debateId } = useParams();
  const debate = useDebate(debateId);
  const state = useDebateStream(debate.data ? debateId : undefined);

  if (debate.error instanceof ApiError && [404, 422].includes(debate.error.status)) {
    return (
      <NotFoundPage
        title="Debate not found"
        detail="It may have expired: the server keeps the most recent debates in memory."
      />
    );
  }

  if (debate.isError) {
    return <Alert title="Couldn't load the debate">{debate.error.message}</Alert>;
  }

  if (!debate.data) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-2/3" />
        <Skeleton className="h-40" />
        <Skeleton className="h-40" />
      </div>
    );
  }

  const estimate = state.report?.estimate ?? debate.data.estimate;
  const disputed = state.judging?.disputed.length ?? 0;

  return (
    <div className="space-y-8">
      <DebateHeader
        title={debate.data.estimate_title}
        location={estimate?.location}
        demo={debate.data.demo}
        state={state}
      />

      <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_300px]">
        <div className="min-w-0 space-y-10">
          {state.status === "connecting" && <Skeleton className="h-40" />}
          <Transcript state={state} estimate={estimate} />

          {state.judging && !state.verdict && (
            <ThinkingCard
              role="judge"
              label={`The judge is weighing ${disputed} disputed ${disputed === 1 ? "line" : "lines"}`}
            />
          )}

          {state.verdict && (
            <VerdictPanel
              verdict={state.verdict}
              estimate={estimate}
              impact={state.report?.impact ?? null}
            />
          )}

          {state.report && (
            <RevisedEstimate
              original={state.report.estimate}
              revised={state.report.revised_estimate}
            />
          )}

          {state.status === "failed" && (
            <Alert title="The debate stopped">
              {state.error}
              {"\n"}
              <Link to="/" className="underline underline-offset-2">
                Start a new one
              </Link>
            </Alert>
          )}

          <UsageDetails usage={state.usage} />
        </div>

        <DebateSidebar state={state} estimate={estimate} />
      </div>
    </div>
  );
}
