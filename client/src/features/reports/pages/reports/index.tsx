import { FileText } from "lucide-react";
import { Link } from "react-router";

import { Alert, Skeleton } from "@/components/ui";
import { ReportList } from "@/features/reports/components";
import { useReports } from "@/features/reports/hooks";
import { Styled } from "@/styled";

export function ReportsPage() {
  const reports = useReports();

  return (
    <div className="space-y-8">
      <header className="space-y-3">
        <p className={Styled.Eyebrow}>Archive</p>
        <h1 className={Styled.DetailTitle}>Reports</h1>
        <p className={Styled.PageLead}>
          Every finished debate is saved on the server: open one to read it again, or export it as
          Markdown, HTML or JSON.
        </p>
      </header>

      {reports.isPending && (
        <div className="space-y-3">
          <Skeleton className="h-20" />
          <Skeleton className="h-20" />
          <Skeleton className="h-20" />
        </div>
      )}

      {reports.isError && <Alert title="Couldn't load the reports">{reports.error.message}</Alert>}

      {reports.data?.length === 0 && (
        <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-line px-6 py-14 text-center">
          <FileText className="size-8 text-ink-faint" aria-hidden />
          <p className="font-medium">No reports yet</p>
          <p className="max-w-sm text-sm text-ink-muted">
            A report is saved as soon as a debate finishes. Try the demo: it needs no API key.
          </p>
          <Link to="/" className="mt-1 text-sm text-judge hover:underline">
            Start a debate
          </Link>
        </div>
      )}

      {reports.data && reports.data.length > 0 && <ReportList reports={reports.data} />}
    </div>
  );
}
