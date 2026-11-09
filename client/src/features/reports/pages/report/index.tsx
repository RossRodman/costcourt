import { useParams } from "react-router";

import { ApiError } from "@/api";
import { Alert, Skeleton } from "@/components/ui";
import { DEMO_MODEL } from "@/constants";
import {
  DebateHeader,
  DebateSidebar,
  RevisedEstimate,
  Transcript,
  UsageDetails,
  VerdictPanel,
} from "@/features/debate/components";
import { stateFromReport } from "@/features/debate/utils/debateState";
import { NotFoundPage } from "@/features/notFound";
import { useReport } from "@/features/reports/hooks";

export function ReportPage() {
  const { reportId } = useParams();
  const report = useReport(reportId);

  if (report.error instanceof ApiError && [404, 422].includes(report.error.status)) {
    return (
      <NotFoundPage
        title="Report not found"
        detail="It may have been deleted from the server's reports folder."
      />
    );
  }

  if (report.isError) {
    return <Alert title="Couldn't load the report">{report.error.message}</Alert>;
  }

  if (!report.data) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-2/3" />
        <Skeleton className="h-40" />
        <Skeleton className="h-40" />
      </div>
    );
  }

  const data = report.data;
  const state = stateFromReport(data);
  const models = Object.values(data.models);
  const demo = models.length > 0 && models.every((model) => model === DEMO_MODEL);

  return (
    <div className="space-y-8">
      <DebateHeader
        title={data.estimate.title}
        location={data.estimate.location}
        demo={demo}
        state={state}
        back={{ to: "/reports", label: "All reports" }}
      />

      <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_300px]">
        <div className="min-w-0 space-y-10">
          <VerdictPanel verdict={data.verdict} estimate={data.estimate} impact={data.impact} />
          <RevisedEstimate original={data.estimate} revised={data.revised_estimate} />
          <Transcript state={state} estimate={data.estimate} />
          <UsageDetails usage={data.usage} />
        </div>

        <DebateSidebar state={state} estimate={data.estimate} />
      </div>
    </div>
  );
}
