import { ArrowRight, MapPin } from "lucide-react";
import { Link } from "react-router";

import { Badge } from "@/components/ui";
import type { ReportSummary } from "@/types";
import { cn } from "@/utils/cn";
import { formatMoney, formatPercent, formatRelative } from "@/utils/format";

interface ReportListProps {
  reports: ReportSummary[];
}

export function ReportList({ reports }: ReportListProps) {
  return (
    <ul className="divide-y divide-line overflow-hidden rounded-2xl border border-line bg-surface">
      {reports.map((report) => (
        <li key={report.id}>
          <ReportRow report={report} />
        </li>
      ))}
    </ul>
  );
}

interface ReportRowProps {
  report: ReportSummary;
}

function ReportRow({ report }: ReportRowProps) {
  const tone =
    report.delta_pct > 0 ? "text-amber-300" : report.delta_pct < 0 ? "text-sky-300" : "text-ink";

  return (
    <Link
      to={`/reports/${report.id}`}
      className="group flex flex-col gap-3 px-5 py-4 transition-colors hover:bg-surface-raised sm:flex-row sm:items-center"
    >
      <div className="min-w-0 flex-1 space-y-1">
        <p className="flex items-center gap-2">
          <span className="truncate font-medium">{report.estimate_title}</span>
          {report.demo && <Badge>demo</Badge>}
        </p>
        <p className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-ink-faint">
          {report.location && (
            <span className="inline-flex items-center gap-1">
              <MapPin className="size-3" aria-hidden />
              {report.location}
            </span>
          )}
          <span>{formatRelative(report.created_at)}</span>
          <span>
            {report.rounds} {report.rounds === 1 ? "round" : "rounds"} · {report.rulings}{" "}
            {report.rulings === 1 ? "ruling" : "rulings"} · {Math.round(report.confidence * 100)}%
            confidence
          </span>
        </p>
      </div>

      <div className="flex items-center gap-4 sm:text-right">
        <div className="text-sm tabular-nums">
          <p className="text-ink-faint line-through decoration-ink-faint/50">
            {formatMoney(report.original_total, report.currency, { whole: true })}
          </p>
          <p>{formatMoney(report.revised_total, report.currency, { whole: true })}</p>
        </div>
        <span className={cn("w-16 text-right text-sm font-medium tabular-nums", tone)}>
          {formatPercent(report.delta_pct, { signed: true })}
        </span>
        <ArrowRight
          className="size-4 text-ink-faint transition-transform group-hover:translate-x-0.5"
          aria-hidden
        />
      </div>
    </Link>
  );
}
