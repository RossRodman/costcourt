import type { ReportFormat } from "@/types";

export interface ReportFormatMeta {
  format: ReportFormat;
  label: string;
  extension: string;
  description: string;
}

export const REPORT_FORMATS: readonly ReportFormatMeta[] = [
  {
    format: "markdown",
    label: "Markdown",
    extension: ".md",
    description: "For GitHub, wikis and docs",
  },
  {
    format: "html",
    label: "HTML",
    extension: ".html",
    description: "One printable page",
  },
  {
    format: "json",
    label: "JSON",
    extension: ".json",
    description: "The full audit trail as data",
  },
];
