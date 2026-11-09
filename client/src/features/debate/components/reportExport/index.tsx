import { Download, ExternalLink, Printer } from "lucide-react";

import { api } from "@/api";
import { Card, CardHeader } from "@/components/ui";
import { REPORT_FORMATS } from "@/constants";

interface ReportExportProps {
  reportId: string;
}

export function ReportExport({ reportId }: ReportExportProps) {
  return (
    <Card>
      <CardHeader title="Report" description="Every argument, ruling and figure, saved." />

      <div className="space-y-3 p-5">
        <a
          href={api.reportExportUrl(reportId, "html")}
          target="_blank"
          rel="noreferrer"
          className="flex h-10 items-center justify-center gap-2 rounded-xl bg-judge px-4 text-sm font-medium text-canvas transition-colors hover:bg-judge/90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-judge"
        >
          <Printer className="size-4" aria-hidden />
          Open printable report
        </a>

        <ul className="divide-y divide-line overflow-hidden rounded-xl border border-line">
          {REPORT_FORMATS.map(({ format, label, extension, description }) => (
            <li
              key={format}
              className="flex items-center transition-colors hover:bg-surface-raised"
            >
              <a
                href={api.reportExportUrl(reportId, format)}
                target="_blank"
                rel="noreferrer"
                title={`Open ${label} in a new tab`}
                className="group flex min-w-0 flex-1 items-center gap-3 px-3 py-2.5"
              >
                <span className="min-w-0 flex-1">
                  <span className="block text-sm">
                    {label} <span className="font-mono text-xs text-ink-faint">{extension}</span>
                  </span>
                  <span className="block truncate text-xs text-ink-faint">{description}</span>
                </span>
                <ExternalLink
                  className="size-4 text-ink-faint transition-colors group-hover:text-ink"
                  aria-hidden
                />
              </a>
              <a
                href={api.reportExportUrl(reportId, format, { download: true })}
                download
                aria-label={`Download ${label}`}
                title={`Download ${extension}`}
                className="flex items-center self-stretch border-l border-line px-3 text-ink-faint transition-colors hover:text-ink"
              >
                <Download className="size-4" aria-hidden />
              </a>
            </li>
          ))}
        </ul>
      </div>
    </Card>
  );
}
